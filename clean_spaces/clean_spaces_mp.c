
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

#ifdef __APPLE__
#define MAP_POPULATE 0
#endif

struct item
{
    struct item* next;
    int fd;
    size_t size;
};

struct context
{
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    struct item* head;
    struct item* items_pool;
    int free_items;
    int done;
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

static void* _worker_proc(struct context* context)
{
int fd;
int col;
int rewrite;
char* input;
char* end;
char* cursor_in;
char* after_last_non_space;
char* cursor_out = NULL;
char* output = NULL;
off_t size;
struct item* item;

    while((item = _wait_for_item(context)) != NULL)
    {
        fd = item->fd;
        size = item->size;
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
            if(rewrite)
            {
                /* since we need a rewrite, we need to copy the beginning of the file
                 * al the way to the first anomaly and fix the current anomally */
                /* in theory teh file could be all tabs... so the output could grow 4 times */
                output = malloc(4 * size);
                if(output)
                {
                    int pre_len;

                    cursor_out = output;

                    if(*cursor_in == '\t')
                    {
                        pre_len = (int)(cursor_in - input);
                        if(pre_len > 1)
                        {
                            memcpy(output, input, pre_len - 1);
                            cursor_out += (pre_len - 1);
                        }
                        /* from now on after_last_non_space point into the output buffer *
                         * technicaly it always have, but up to now the output buffer was
                         * also the input buffer */
                        pre_len = (int)(after_last_non_space - input);
                        after_last_non_space = output;
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
                            memcpy(output, input, pre_len);
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
                        assert(0);
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
                    if(cursor_out == output)
                    {
                        /* empty_file */
                        ftruncate(fd, 0);
                    }
                    else
                    {
                    ssize_t written;

                        written = write(fd, output, (size_t)(cursor_out - output));
                        if(written != (ssize_t)(cursor_out - output))
                        {
                            assert(0);
                        }
                        ftruncate(fd, written);
                    }
                    close(fd);
                    free(output);
                }
                else
                {
                    assert(0);
                }
            }
            else
            {
                close(fd);
            }
            munmap(input, size);
        }
        else
        {
            close(fd);
        }
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

static int _clean_one_file(struct context* context, char* filename)
{
int rc = 0;
int fd;
int col;
int rewrite = 0;
struct item* item;
char* input;
char* end;
char* cursor_in;
char* after_last_non_space;
char* cursor_out = NULL;
char* output = NULL;
off_t size = 0;
struct stat s;

    /* look for the extension, ignore pure dot filename */
    cursor_in = filename + strlen(filename);
    while(cursor_in > filename && *cursor_in != '.')
    {
        cursor_in -= 1;
    }
    if(cursor_in > filename)
    {
        /* check that the extention is candidat for filtering */
        if(_is_filter_candidat(cursor_in + 1))
        {
            if(stat(filename, &s))
            {
                return 1;
            }
            /* we filter only non-zero sized regular file */
            if(S_ISREG(s.st_mode))
            {
                size = s.st_size;
            }
            if(size)
            {
                fd = open(filename, O_RDWR);
                if(fd != -1)
                {
                    item = _get_item(context);
                    item->fd = fd;
                    item->size = size;
                    _post_item(context, item);
                }
                else
                {
                    rc = 1;
                }
            }
        }
    }
    return rc;
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
int nb_workers;
struct context context;
pthread_t* workers_tid;
char filename[2048];
pthread_mutexattr_t mutex_attribute;
pthread_condattr_t cond_attribute;

    memset(&context, 0, sizeof(struct context));
    nb_workers = sysconf(_SC_NPROCESSORS_ONLN);
    if(nb_workers < 1)
    {
        nb_workers = 1;
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
                nb_workers = atoi(argv[i]);
                if(nb_workers < 0 || nb_workers > 512)
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
    workers_tid = calloc(nb_workers, sizeof(pthread_t));

    pthread_mutexattr_init(&mutex_attribute);
    pthread_condattr_init(&cond_attribute);
    pthread_mutex_init(&context.mutex, &mutex_attribute);
    pthread_cond_init(&context.cond, &cond_attribute);

    for(i = 0; i < nb_workers; i++)
    {
        pthread_create(&(workers_tid[i]), NULL, (void* (*)(void*))_worker_proc, &context);
    }

    /* yes this is unsafe since we 'hope' that no line will be more than 2048,
     * but then we don't have to deal with cleaning \n... so that will do
     * for reasonable use (and this is a lmited-use tool, not a 'product')
    */
    while(fgets(filename, 2048, stdin))
    {
    int len = strlen(filename);

        if(len)
        {
            if(filename[len-1] == '\n')
            {
                filename[len-1] = 0;
            }
            _clean_one_file(&context, filename);
        }
    }
    context.done = 1;
    pthread_cond_broadcast(&context.cond);
    for( i = 0; i < nb_workers; i++)
    {
        pthread_join(workers_tid[i], NULL);
    }
    return rc;
}
