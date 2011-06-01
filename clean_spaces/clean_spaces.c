
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <pthread.h>
#include <errno.h>

#ifdef __APPLE__
#define MAP_POPULATE 0
#endif

struct item
{
    struct item* next;
    char* filename;
};

struct context
{
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    struct item* head;
    struct item* items_pool;
    int free_items;
    int done;
    int nb_workers;
    char* output;
    int allocated_output;
};


static char* filter[] =
{
    "c","cpp","cxx","h","hrc","hxx","idl","inl","java","map","pl","pm","sdi","sh","src","tab","xcu","xml"
};

static int _is_filter_candidat(char* extension)
{
    int first = 0;
    int last = sizeof(filter)/sizeof(char*);
    int next;
    int cmp;
    char* cursor;

    while(last > first)
    {
        next = (first + last) >> 1;
        cursor = filter[next];
        cmp = strcmp(cursor, extension);
        if(cmp > 0)
        {
            last = next;
        }
        else if(cmp < 0)
        {
            first = next + 1;
        }
        else
        {
            return 1;
        }
    }
    return 0;
}

static struct item* _wait_for_item(struct context* context)
{
struct item* item;

    pthread_mutex_lock(&context->mutex);
    while(context->head == NULL)
    {
        if(context->done)
        {
            break;
        }
        pthread_cond_wait(&context->cond, &(context->mutex));
    }
    item = context->head;
    if(item)
    {
        context->head = item->next;
        if(item->next)
        {
            pthread_cond_broadcast(&context->cond);
        }
    }
    pthread_mutex_unlock(&context->mutex);
    return item;
}

int _post_item(struct context* context, struct item* item)
{
    pthread_mutex_lock(&context->mutex);
    item->next = context->head;
    context->head = item;
    if(!item->next)
    {
        pthread_cond_signal(&context->cond);
    }
    pthread_mutex_unlock(&context->mutex);
}

static int _do_one_file(char* filename, char** output, int* allocated_output)
{
int fd;
int col;
int rewrite;
char* input;
char* end;
char* cursor_in;
char* after_last_non_space;
char* cursor_out = NULL;
off_t size = 0;
struct stat s;

//  fprintf(stderr,"process %s\n", filename);
    /* look for the extension, ignore pure dot filename */
    cursor_in = filename + strlen(filename);
    while(cursor_in > filename && *cursor_in != '.')
    {
        cursor_in -= 1;
    }
    if(cursor_in == filename)
    {
        return 0;
    }
    /* check that the extention is candidat for filtering */
    if(!_is_filter_candidat(cursor_in + 1))
    {
        return 0;
    }
    if(stat(filename, &s))
    {
        fprintf(stderr, "*** Error on stat for %s\n", filename);
        return 0;
    }
    /* we filter only non-zero sized regular file */
    if(S_ISREG(s.st_mode))
    {
        size = s.st_size;
    }
    if(!size)
    {
        return 0;
    }
    fd = open(filename, O_RDONLY);
    if(fd != -1)
    {
        input = mmap( NULL, size, PROT_READ, MAP_PRIVATE | MAP_POPULATE, fd, 0);
        if(input != MAP_FAILED)
        {
            cursor_in = input;
            end = input;
            end += size;
            after_last_non_space = cursor_in;
            col = 0;
            rewrite = 0;
            /* first find the first occurence if any of things needing a rewrite */
            while(cursor_in < end)
            {
                /* short-cut the most common case */
                if(*cursor_in > 32)
                {
                    cursor_in += 1;
                    col += 1;
                    after_last_non_space = cursor_in;
                }
                else if(*cursor_in == '\n')
                {
                    if(cursor_in != after_last_non_space)
                    {
                        rewrite = 1;
                        break;
                    }
                    else
                    {
                        cursor_in += 1;
                        after_last_non_space = cursor_in;
                        col = 0;
                    }
                }
                else if(*cursor_in == ' ')
                {
                    cursor_in += 1;
                    col += 1;
                }
                else if(*cursor_in == '\t')
                {
                    rewrite = 1;
                    break;
                }
                else
                {
                    cursor_in += 1;
                    col += 1;
                    after_last_non_space = cursor_in;
                }
            }
            close(fd);
            if(rewrite)
            {
                /* since we need a rewrite, we need to copy the beginning of the file
                 * al the way to the first anomaly and fix the current anomally */
                /* in theory teh file could be all tabs... so the output could grow 4 times */
                if((4 * size) >= *allocated_output)
                {
                    int new_size = (((size+1) * 4) + 32768) & ~32767; /* round up to the next 32K */

                    *output = realloc(*output, new_size);
//                  fprintf(stderr, "realloc from %d to %d\n", allocated_output, new_size);
                    *allocated_output = new_size;
                }
                if(*output)
                {
                    int pre_len = 0;

                    cursor_out = *output;

                    if(*cursor_in == '\t')
                    {
                        pre_len = (int)(cursor_in - input);
                        if(pre_len > 1)
                        {
                            memcpy(*output, input, pre_len - 1);
                            cursor_out += (pre_len - 1);
                        }
                        /* from now on after_last_non_space point into the output buffer *
                         * technicaly it always have, but up to now the output buffer was
                         * also the input buffer */
                        pre_len = (int)(after_last_non_space - input);
                        after_last_non_space = *output;
                        after_last_non_space += pre_len;

                        /* expend the tab to the correct number of spaces */
                        pre_len = (~col & 3);
                        switch( (unsigned char)pre_len)
                        {
                        case 3:
                            *cursor_out++ = ' ';
                        case 2:
                            *cursor_out++ = ' ';
                        case 1:
                            *cursor_out++ = ' ';
                        default:
                            *cursor_out++ = ' ';
                        }
                        col += pre_len + 1;
                        cursor_in += 1;
                    }
                    else if(*cursor_in == '\n')
                    {
                        pre_len = (int)(after_last_non_space - input);
                        if(pre_len > 0)
                        {
                            memcpy(*output, input, pre_len);
                            cursor_out += (pre_len);
                        }
                        *cursor_out++ = '\n';
                        cursor_in += 1;
                        after_last_non_space = cursor_out;
                        col = 0;
                    }
                    else
                    {
                        /* that should not happen */
                        abort();
                    }
                    /* clean-up the rest of the file as-needed*/
                    while(cursor_in < end)
                    {
                        /* short-cut the most common case */
                        if(*cursor_in > 32)
                        {
                            *cursor_out++ = *cursor_in++;
                            col += 1;
                            after_last_non_space = cursor_out;
                        }
                        else if(*cursor_in == '\n')
                        {
                            if(cursor_out != after_last_non_space)
                            {
                                *after_last_non_space++ = *cursor_in++;
                                cursor_out = after_last_non_space;
                            }
                            else
                            {
                                *cursor_out++ = *cursor_in++;
                                after_last_non_space = cursor_out;
                            }
                            col = 0;
                        }
                        else if(*cursor_in == ' ')
                        {
                            *cursor_out++ = *cursor_in++;
                            col += 1;
                        }
                        else if(*cursor_in == '\t')
                        {
                            pre_len = (~col & 3);
                            /* we cast to unsigned char to help to compiler optimize the case jump table */
                            switch( (unsigned char)pre_len)
                            {
                            case 3:
                                *cursor_out++ = ' ';
                            case 2:
                                *cursor_out++ = ' ';
                            case 1:
                                *cursor_out++ = ' ';
                            default:
                                *cursor_out++ = ' ';
                            }
                            col += pre_len + 1;
                            cursor_in += 1;
                        }
                        else
                        {
                            *cursor_out++ = *cursor_in++;
                            col += 1;
                            after_last_non_space = cursor_out;
                        }
                    }
                    if(after_last_non_space != cursor_out)
                    {
                        /* we have space on the last line without \n at the end */
                        *after_last_non_space++ = '\n';
                        cursor_out = after_last_non_space;
                    }
                    fd = open(filename, O_WRONLY | O_TRUNC);
                    if(fd != -1)
                    {
                        if(cursor_out == *output)
                        {
                            /* empty_file */
                        }
                        else
                        {
                            ssize_t written;

                            written = write(fd, *output, (size_t)(cursor_out - *output));
                            if(written != (ssize_t)(cursor_out - *output))
                            {
                                fprintf(stderr, "*** Error writing %s\n", filename);
                            }
                        }
                        close(fd);
                    }
                    else
                    {
                        fprintf(stderr, "*** Error re-opening %s for write\n", filename);
                    }
                }
                else
                {
                    abort();
                }
            }
            munmap(input, size);
        }
        else
        {
            close(fd);
        }
    }
    else
    {
        fprintf(stderr, "*** Error on open for %s\n", filename);
    }
    return 0;
}

static void* _worker_proc(struct context* context)
{
int rc = 0;
char* output = NULL;
int allocated_output = 1024*1024;
struct item* item;

    output = malloc(allocated_output);
    while((item = _wait_for_item(context)) != NULL)
    {
        _do_one_file(item->filename, &output, &allocated_output);
    }
    return NULL;
}

static struct item* _get_item(struct context* context)
{
struct item* item;

    if(context->free_items <= 0)
    {
        /* yes this leak... we we don't care. it is not worth the effort
         * to synchornize stuff to know when to recycle an item
         * i.e when it is safe to free a items_pool block
         */
        context->items_pool = (struct item*)calloc(4096, sizeof(struct item));
        context->free_items = 4095;
    }
    item = &(context->items_pool[context->free_items]);
    context->free_items -= 1;
    return item;
}

static char* _consume_input(struct context* context, char* fn_cursor, char* fn_tail)
{
char* filename;
struct item* item;

    while(fn_cursor <= fn_tail)
    {
        filename = fn_cursor;
        while(*fn_cursor && *fn_cursor != '\n')
        {
            fn_cursor += 1;
        }
        if(*fn_cursor =='\n')
        {
            *fn_cursor = 0;
            fn_cursor += 1;
            if(context->nb_workers > 1)
            {
                item = _get_item(context);
                item->filename = filename;
//              fprintf(stderr, "post %s\n", filename);
                _post_item(context, item);
            }
            else
            {
                _do_one_file(filename, &context->output, &context->allocated_output);
            }
        }
        else
        {
            fn_cursor = filename;
            break;
        }
    }
    return fn_cursor;
}

static void _usage(void)
{
    puts("Usage: clean_spaces [-p <nb_of_worker_thread>\n");
    puts("stdin contain the list of file to process (one file per line)\n");
}

int main(int argc, char** argv)
{
int rc = 0;
int i;
struct context context;
pthread_t* workers_tid;
char filename[2048];
pthread_mutexattr_t mutex_attribute;
pthread_condattr_t cond_attribute;
char* fn_buffer;
/* Note:FN_BUFFER_SIZE has been sized to fit the largest output expected
 * from git ls-files by a margin factor > 4 so we don't care for
 * case where stdin is biger than that. actually we fail with rc=1 if that
 * happen
 */
#define FN_BUFFER_SIZE (2*1024*1024)
char* fn_cursor;
char* fn_head;
char* fn_tail;
int fn_used = 0;
int fn_read = 0;
char* output = NULL;

    memset(&context, 0, sizeof(struct context));
    context.nb_workers = sysconf(_SC_NPROCESSORS_ONLN);
    if(context.nb_workers < 1)
    {
        context.nb_workers = 1;
    }

    for( i = 1; !rc && i < argc; i++)
    {
        if(!strcmp(argv[i], "-h"))
        {
            _usage();
            return 0;
        }
        else if(!strcmp(argv[i], "-p"))
        {
            i += 1;
            if( i < argc)
            {
                context.nb_workers = atoi(argv[i]);
                if(context.nb_workers < 0 || context.nb_workers > 512)
                {
                    _usage();
                    return 8;
                }
            }
            else
            {
                _usage();
                return 8;
            }
        }
        else
        {
            _usage();
            return 8;
        }
    }

    if(context.nb_workers > 1)
    {
        workers_tid = calloc(context.nb_workers, sizeof(pthread_t));

        pthread_mutexattr_init(&mutex_attribute);
        pthread_condattr_init(&cond_attribute);
        pthread_mutex_init(&context.mutex, &mutex_attribute);
        pthread_cond_init(&context.cond, &cond_attribute);

        for(i = 0; i < context.nb_workers; i++)
        {
            pthread_create(&(workers_tid[i]), NULL, (void* (*)(void*))_worker_proc, &context);
        }
    }
    else
    {
        context.allocated_output = 1024*1024;
        context.output = malloc(context.allocated_output);
    }

    fn_buffer = malloc(FN_BUFFER_SIZE);
    fn_tail = fn_cursor = fn_buffer;

    for(;;)
    {
        fn_read = read(STDIN_FILENO, fn_buffer + fn_used, FN_BUFFER_SIZE - fn_used);
        if(fn_read > 0)
        {
            fn_used += fn_read;
            fn_tail += fn_read;
            *fn_tail = 0;
            fn_cursor = _consume_input(&context, fn_cursor, fn_tail);
            if(fn_used == FN_BUFFER_SIZE)
            {
                rc = 1;
                break;
            }
        }
        else
        {
            if(fn_read == 0)
            {
                break;
            }
            else
            {
                if(errno != EINTR)
                {
                    rc = -1;
                    break;
                }
            }
        }
    }
    if(context.nb_workers > 1)
    {
        context.done = 1;
        pthread_cond_broadcast(&context.cond);
        for( i = 0; i < context.nb_workers; i++)
        {
            pthread_join(workers_tid[i], NULL);
        }
    }
    return rc;
}
