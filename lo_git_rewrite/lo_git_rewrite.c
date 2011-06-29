
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <pthread.h>
#include <errno.h>
#include <fcntl.h>

static struct buffer
{
    char* data;
    char* head;
    char* tail;
    char* cursor;
    char* workspace;
    int allocated_workspace;
    int free;
    int allocated;
    int nb_commit;
    int nb_blob;
    int nb_cleaned;
    int nb_not_cleaned;
    int nb_tag;
} g_buffer;

#define kBUFFER_SIZE (10*1024*1024)

static void _realign_buffer(struct buffer* buffer)
{
int offset = 0;
int used;
char* d;
char* s;

    fprintf(stderr, "commit:%d tag:%d blob:%d cleaned:%d not_cleaned:%d\n",
            buffer->nb_commit, buffer->nb_tag, buffer->nb_blob, buffer->nb_cleaned, buffer->nb_not_cleaned);
//    fprintf(stderr, "-> realligned buffer: datqa:%p head:%p, cursor:%p tail:%p free:%d nb_commit=%d\n",
//            buffer->data, buffer->head, buffer->cursor, buffer->tail, buffer->free, buffer->nb_commit);
    if(buffer->head > buffer->data)
    {
        offset = buffer->cursor - buffer->head;
        used = (buffer->tail - buffer->head);
//        fprintf(stderr, "realligned buffer: free=%d offset=%d used=%d\n", buffer->free, offset, used);
        d = buffer->data;
        s = buffer->head;
        while(s < buffer->tail)
        {
            *d++ = *s++;
        }
        buffer->head = buffer->data;
        buffer->cursor = buffer->head + offset;
        buffer->tail = buffer->head + used;
        buffer->free = kBUFFER_SIZE - used;
    }
//    fprintf(stderr, "<- realligned buffer: datqa:%p head:%p, cursor:%p tail:%p free=%d\n",
//            buffer->data, buffer->head, buffer->cursor, buffer->tail, buffer->free);
}

static void _read_more(struct buffer* buffer)
{
int received;

    if(buffer->free < 4096)
    {
        _realign_buffer(buffer);
    }
  Retry:
    assert(buffer->free > 0);
    received = read(STDIN_FILENO, buffer->tail, buffer->free);
    if(received > 0)
    {
        buffer->tail += received;
        buffer->free -= received;
    }
    else
    {
        if(received == 0)
        {
            exit(100);
        }
        else
        {
            if(errno != EINTR)
            {
                fprintf(stderr, "_read_more error:%d\n", errno);
                exit(1);
            }
            else
            {
                goto Retry;
            }
        }
    }
}

static void _read_in_full(struct buffer* buffer, int len)
{
    while(buffer->cursor + len >= buffer->tail)
    {
        _read_more(buffer);
    }
}

static void _write_in_full(char* data, int len)
{
    int written;
    int done = 0;

//    write(STDERR_FILENO, data + done, len - done);
    if(len == 0)
    {
        return;
    }
    assert(len > 0);
    do
    {
      Retry:
        written = write(STDOUT_FILENO, data + done, len - done);
        if(written > 0)
        {
            done += written;
        }
        else
        {
            if(written == -1 && errno == EINTR)
            {
                goto Retry;
            }
            fprintf(stderr, "_writ_in_full error:%d\n", errno);
            exit(1);
        }
    }
    while(done < len);
}

static void _copy_line(struct buffer* buffer)
{
int pos = 0;
int space_count = 0;
int id_pos = 0;
int id_end_pos = -1;

    while(buffer->cursor[pos] != '\n')
    {
        if(buffer->cursor[pos] == ' ')
        {
            space_count += 1;
            if(space_count == 2)
            {
                id_end_pos = pos;
            }
        }
        else if(buffer->cursor[pos] == ':')
        {
            if(space_count == 1)
            {
                id_pos = pos + 1;
            }
        }
        pos += 1;
        if(buffer->cursor + pos >= buffer->tail)
        {
            _read_more(buffer);
        }
    }
    if(id_pos)
    {
        if(id_end_pos == -1)
        {
            _write_in_full(buffer->cursor, pos);
            _write_in_full("0\n", 2);
        }
        else
        {
            _write_in_full(buffer->cursor, id_end_pos);
            _write_in_full("0", 1);
            _write_in_full(buffer->cursor + id_end_pos, (pos + 1) - id_end_pos);
        }
    }
    else
    {
        _write_in_full(buffer->cursor, pos + 1);
    }
    buffer->cursor += pos + 1;
    if(buffer->cursor >= buffer->tail)
    {
        _read_more(buffer);
    }

}

static void _copy_data(struct buffer* buffer)
{
int pos = 0;
int data_len;
char* cursor;

    while(buffer->cursor[pos] != '\n')
    {
        pos += 1;
        if(buffer->cursor + pos >= buffer->tail)
        {
            _read_more(buffer);
        }
    }
    cursor = buffer->cursor + 5;
    data_len = 0;
    while(*cursor != '\n')
    {
        data_len *= 10;
        data_len += *cursor - '0';
        cursor += 1;
    }
    _write_in_full(buffer->cursor, pos + 1);
    buffer->cursor += pos + 1;
    if(buffer->cursor + (data_len) >= buffer->tail)
    {
        _read_in_full(buffer, data_len);
    }
    _write_in_full(buffer->cursor, data_len);
    buffer->cursor += data_len;
}

static void _write_int(int len)
{
    char temp[13];
    char* cursor;

    cursor = temp + 12;
    *cursor-- = 0;
    *cursor = '\n';
    do
    {
        cursor -= 1;
        *cursor = (len % 10) + '0';
        len /= 10;
    }
    while(len);
    _write_in_full(cursor, strlen(cursor));
}

int _convert_data(struct buffer* buffer, char* input, int len)
{
int col;
int pre_len;
char* end;
char* cursor_in;
char* after_last_non_space;
char* cursor_out = buffer->workspace;

    cursor_in = input;
    end = input;
    end += len;
    after_last_non_space = cursor_out;
    col = 0;
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
            memset(cursor_out, ' ', 4);
            cursor_out += pre_len + 1;
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
    return cursor_out - buffer->workspace;
}

static void _process_blob(struct buffer* buffer)
{
int h1;
int h2;
int data_len;
int new_len;

    buffer->cursor = buffer->head;
    if(buffer->head + 12 > buffer->tail)
    {
        _read_in_full(buffer, 12);
    }
    if(memcmp(buffer->head, "blob\nmark :", 11))
    {
        fprintf(stderr, "unknown command %11.11s\n", buffer->head);
        exit(1);
    }
    buffer->cursor += 11;
    while(*buffer->cursor != '\n')
    {
        buffer->cursor += 1;
        if(buffer->cursor >= buffer->tail)
        {
            _read_more(buffer);
        }
    }
    h1 = buffer->cursor - buffer->head;
    if(buffer->cursor + 7 >= buffer->tail)
    {
        _read_in_full(buffer, 7);
    }
    if(memcmp(buffer->cursor, "\ndata ", 6))
    {
        fprintf(stderr, "unknown command %6.6s\n", buffer->cursor);
        exit(1);
    }
    buffer->cursor += 6;
    data_len = 0;
    while(*buffer->cursor != '\n')
    {
        data_len *= 10;
        data_len += *buffer->cursor - '0';
        buffer->cursor += 1;
        if(buffer->cursor >= buffer->tail)
        {
            _read_more(buffer);
        }
    }
    h2 = buffer->cursor - buffer->head;
    if(buffer->cursor + (data_len + 1) >= buffer->tail)
    {
        _read_in_full(buffer, data_len + 1);
    }
    _write_in_full(buffer->head, h1);
    _write_in_full("0", 1);
    _write_in_full(buffer->head + h1, data_len + (h2 - h1) + 2);
    new_len = _convert_data(buffer, buffer->head + h2 + 1, data_len);
    _write_in_full(buffer->head, h1);
    _write_in_full("1", 1);
    _write_in_full(buffer->head + h1, 6);
    _write_int(new_len);
    _write_in_full(buffer->workspace, new_len);
    _write_in_full("\n",1);
    buffer->head += data_len + h2 + 2;
    buffer->cursor = buffer->head;
    buffer->nb_blob += 1;
}

static char* filter[] =
{
    "c","cpp","cxx","h","hrc","hxx","idl","inl","java","map","pl","pm","sdi","sh","src","tab","xcu","xml"
};

static int _is_filter_candidat(char* fn, int len)
{
int first = 0;
int last = sizeof(filter)/sizeof(char*);
int next;
int cmp;
char* cursor;
char* extension;
char temp[10];

    len -= 1;
    cursor = fn + len;
    extension = temp + 9;
    *extension-- = 0;

    while(extension > temp && len > 0)
    {
        if(*cursor == '.')
        {
            break;
        }
        *extension-- = *cursor--;
        len -= 1;
    }
    if(*cursor != '.')
    {
        return 0;
    }
    extension += 1;

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

static void _process_commit_action(struct buffer* buffer)
{
    int i = 0;
    int id_pos = -1;
    int mode_pos = -1;
    int path_pos = -1;

    while(buffer->cursor[i] != '\n')
    {
        if(buffer->cursor[i] == ' ')
        {
            if(mode_pos < 0 )
            {
                mode_pos = i + 1;
            }
            else if(id_pos < 0)
            {
                id_pos = i + 1;
            }
            else if(path_pos < 0)
            {
                path_pos = i + 1;
            }
            else
            {
                abort();
            }
        }
        i += 1;
        if(buffer->cursor + i >= buffer->tail)
        {
            _read_more(buffer);
        }
    }
    _write_in_full(buffer->cursor, path_pos - 1);
    if(_is_filter_candidat(buffer->cursor + path_pos, i - path_pos))
    {
        _write_in_full("1", 1);
        buffer->nb_cleaned += 1;
    }
    else
    {
        _write_in_full("0", 1);
        buffer->nb_not_cleaned += 1;
    }
    _write_in_full(buffer->cursor + path_pos - 1, i - path_pos + 2);
    buffer->cursor += i + 1;
}

static void _process_commit(struct buffer* buffer)
{
    buffer->cursor = buffer->head;
    while(*buffer->cursor != 'd')
    {
        _copy_line(buffer);
    }
    _copy_data(buffer);
    while(*buffer->cursor != '\n')
    {
        switch(*buffer->cursor)
        {
        case 'f':
        case 'm':
        case 'D':
            _copy_line(buffer);
            break;
        case 'M':
            _process_commit_action(buffer);
            break;
        default:
            fprintf(stderr, "unrecognized commit action '%.120s'\n", buffer->cursor - 20);
            exit(1);
        }
        if(buffer->cursor  >= buffer->tail)
        {
            _read_more(buffer);
        }

    }
    buffer->nb_commit += 1;
    buffer->head = buffer->cursor;
}

static void _process_tag(struct buffer* buffer)
{
    buffer->cursor = buffer->head;
    while(*buffer->cursor != 'd')
    {
        _copy_line(buffer);
    }
    _copy_data(buffer);
    buffer->nb_tag += 1;
    buffer->head = buffer->cursor;
}

static void _consume_input(struct buffer* buffer)
{
    do
    {
        switch(*(buffer->head))
        {
        case 'b':
            _process_blob(buffer);;
            break;
        case 'c':
            _process_commit(buffer);
            break;
        case 't':
            _process_tag(buffer);
            break;
        default:
            _copy_line(buffer);
            buffer->head = buffer->cursor;
            break;
        }

    }
    while(buffer->head < buffer->tail);
}

int main(int argc, char** argv)
{
int rc = 0;
int received = 0;
struct buffer* buffer = &g_buffer;

    buffer->data = malloc(kBUFFER_SIZE + 1);
    if(!buffer->data)
    {
        return ENOMEM;
    }
    buffer->workspace = malloc(2 * kBUFFER_SIZE);
    if(!buffer->workspace)
    {
        return ENOMEM;
    }
    buffer->head = buffer->data;
    buffer->tail = buffer->data;
    buffer->cursor = buffer->data;
    buffer->free = kBUFFER_SIZE;
    buffer->allocated = kBUFFER_SIZE;


    while(!rc)
    {
        if(buffer->free < 4096)
        {
            _realign_buffer(buffer);
        }
        if(buffer->free > 0)
        {
          Retry:
            received = read(STDIN_FILENO, buffer->tail, buffer->free);
            if(received > 0)
            {
                buffer->tail += received;
                buffer->free -= received;
            }
            else
            {
                if(received == 0)
                {
                    return 0;
                }
                else
                {
                    if(errno == EINTR)
                    {
                        goto Retry;
                    }
                    else
                    {
                        return errno;
                    }
                }
            }
        }
        _consume_input(buffer);
    }
    fprintf(stderr, "commit:%d tag:%d blob:%d cleaned:%d not_cleaned:%d\n",
            buffer->nb_commit, buffer->nb_tag, buffer->nb_blob, buffer->nb_cleaned, buffer->nb_not_cleaned);

    return rc;
}
