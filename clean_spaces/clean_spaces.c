
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

#ifdef __APPLE__
#define MAP_POPULATE 0
#endif

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
            //printf("keep %s\n", extension);
            return 1;
        }
    }
    //printf("exclude %s\n", extension);
    return 0;
}

static int _clean_one_file(char* filename)
{
int rc = 0;
int fd;
int col;
int rewrite = 0;
char* input;
char* end;
char* cursor_in;
char* after_last_non_space;
char* cursor_out = NULL;
char* output = NULL;
off_t size = 0;
struct stat s;

    //printf("process %s\n", filename);
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
                //printf("size = %d\n", (int)size);
            }
            if(size)
            {
                fd = open(filename, O_RDONLY);
                if(fd != -1)
                {
                    //printf("opened %s\n", filename);
                    input = mmap( NULL, size, PROT_READ, MAP_PRIVATE | MAP_POPULATE, fd, 0);
                    if(input != MAP_FAILED)
                    {
                        close(fd);
                        cursor_in = input;
                        end = input;
                        end += size;
                        after_last_non_space = cursor_in;
                        col = 0;
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
                            //printf("rewrite %s\n", filename);
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
                                    /* note: this does not apply to empty file */
                                    *after_last_non_space++ = '\n';
                                    cursor_out = after_last_non_space;
                                }
                                fd = open(filename, O_WRONLY | O_TRUNC);
                                if(fd != -1)
                                {
                                    if(cursor_out == output)
                                    {
                                        /* empty_file */
                                    }
                                    else
                                    {
                                    ssize_t written;

                                        written = write(fd, output, (size_t)(cursor_out - output));
                                        if(written != (ssize_t)(cursor_out - output))
                                        {
                                            rc = 1;
                                        }
                                    }
                                    close(fd);
                                }
                                else
                                {
                                    rc = 1;
                                }
                                free(output);
                            }
                            else
                            {
                                rc = 1;
                            }
                        }
                        else
                        {
                            //printf("leave %s\n", filename);
                        }
                        munmap(input, size);
                    }
                    else
                    {
                        rc = 1;
                    }
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

int main(int argc, char** argv)
{
    char* filename;
    int i;
    int rc = 0;

    //printf("start argc=%d\n", argc);
    for( i = 1; !rc && i < argc; i++)
    {
        filename = argv[i];
        rc = _clean_one_file(filename);
    }
    return rc;
}
