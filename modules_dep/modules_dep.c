

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct module_ref
{
   struct module_ref* next;
   struct module* module;
};

struct module
{
    struct module* next;
    struct module_ref* parents;
    struct module_ref* children;
    char* name;
    char* list_parents;
    int traversed;
};

#define SHOW_F_PARENTS  (int)(1<<0)
#define SHOW_F_CHILDREN (int)(1<<1)
#define SHOW_F_UNIQUE   (int)(1<<2)

static int _compare_module(struct module** a, struct module** b)
{
    return strcmp((*a)->name, (*b)->name);
}

static struct module* _load_module_deps(char* filename, int verbose)
{
FILE* fp;
struct module* module = NULL;
char* children_start;
char buffer[4096]; /* ok ugly, we should really be dynamic here... but that will do for now */

    fp = fopen(filename, "r");
    if(fp)
    {
        if(verbose)
        {
            fprintf(stderr, "Processing %s\n", filename);
        }
      Retry:
        if(fgets(buffer, 4096, fp))
        {
            char* cursor_in = buffer;
            char* cursor_out = buffer;
            size_t len;
            if(*cursor_in == '#')
            {
                /* argh comment line skip it */
                goto Retry;
            }
            while(*cursor_in && !isblank(*cursor_in))
            {
                cursor_in += 1;
            }
            if(cursor_in == cursor_out)
            {
                fprintf(stderr, "error parsing %s\n", filename);
                exit(1);
            }
            while(isblank(*cursor_in))
            {
                cursor_in += 1;
            }
            /* here we should be on the module name */
            while(*cursor_in && !isblank(*cursor_in) && *cursor_in != ':')
            {
                *cursor_out++ = *cursor_in++;
            }
            *cursor_out++ = 0;
            children_start = cursor_out;
            /* position ourselves to the begenning of the list of dep */
            while(isblank(*cursor_in) || *cursor_in == ':')
            {
                cursor_in ++;
            }
            while(*cursor_in)
            {
            char* retry_cursor = cursor_out;

                while(*cursor_in && !isblank(*cursor_in))
                {
                    if(*cursor_in == ':')
                    {
                        /* optional dep: just ignore that part */
                        *cursor_out = 0;
                        cursor_out = retry_cursor;
                        if(!strcmp(retry_cursor, "SUN"))
                        {
                            /* skip SUN: dep alltogether */
                            while(*cursor_in && !isblank(*cursor_in))
                            {
                                cursor_in++;
                            }
                            break;
                        }
                    }
                    else
                    {
                        *cursor_out++ = *cursor_in;
                    }
                    cursor_in += 1;
                }
                if(retry_cursor != cursor_out)
                {
                    *cursor_out++ = 0;
                }
                while(isblank(*cursor_in))
                {
                    cursor_in += 1;
                }
            }
            *cursor_out = 0;
            module = calloc(1, sizeof(struct module));
            module->name = strdup(buffer);
            len = (size_t)(cursor_out - children_start);
            if(len < 6)
            {
                module->list_parents = strdup("NULL\n");
            }
            else
            {
                char* tail_indicator = cursor_out;
                tail_indicator -= 6;
                if(strcmp(tail_indicator, "NULL\n"))
                {
                    fprintf(stderr, "error Parsing %s (%s)\n", filename, tail_indicator);
                    exit(1);
                }
                module->list_parents = malloc(len);
                memcpy(module->list_parents, children_start, len);
            }
        }
        else
        {
            fprintf(stderr, "error reading %s\n", filename);
            exit(1);
        }
    }
    else
    {
        fprintf(stderr, "error opening %s\n", filename);
        exit(1);
    }
    fclose(fp);
    return module;
}

struct module* _lookup_module(char* name, struct module** modules, int nb_modules)
{
    int first = 0;
    int last = nb_modules;
    int cmp;
    struct module* cursor;

    while(last > first)
    {
        int next = (last + first ) >> 1;

        cursor = modules[next];
        cmp = strcmp(cursor->name, name);
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
            return cursor;
        }
    }
    return NULL;
}

static int _resolve_dep(struct module** modules, int nb_modules)
{
int rc = 0;
int i;
struct module* module;
struct module* parent;
char * cursor;
struct module_ref* mr;

    qsort(modules, nb_modules, sizeof(struct module*), (int(*)(const void *, const void *))_compare_module);

    for(i = 0; i < nb_modules; i++)
    {
        module = modules[i];
        cursor = module->list_parents;
        while(cursor && *cursor)
        {
            parent = _lookup_module(cursor, modules, nb_modules);
            if(parent)
            {
                mr = calloc(1, sizeof(struct module_ref));
                mr->module = parent;
                mr->next = module->parents;
                module->parents = mr;
                mr = calloc(1, sizeof(struct module_ref));
                mr->module = module;
                mr->next = parent->children;
                parent->children = mr;
            }
            else
            {
                if(strcmp(cursor, "NULL\n"))
                {
                    fprintf(stderr, "Error: depenecy %s of module %s does not have a known build.lst associated to it\n", cursor, module->name);
                }
            }
            cursor += strlen(cursor) + 1;
        }
    }
    return rc;
}

static int _print_module(struct module* module, int show, int level)
{
int rc = 0;
int i;
struct module_ref* cursor = NULL;

    if(show & SHOW_F_UNIQUE)
    {
        if(module->traversed)
        {
            return rc;
        }
        module->traversed = 1;
    }
    if(level > 512)
    {
        fprintf(stderr, "Error runaway recursion... recursive dependencies ?\n");
        exit(1);
    }
    for(i = 0; i < level - 1; i++)
    {
        printf("   ");
    }
    if(i < level)
    {
        printf("  + %s\n", module->name);
    }
    else
    {
        printf("%s\n", module->name);
    }
    if(show & SHOW_F_CHILDREN)
    {
        cursor = module->children;
    }
    if(show & SHOW_F_PARENTS)
    {
        cursor = module->parents;
    }
    while(cursor)
    {
        _print_module(cursor->module, show, level + 1);
        cursor = cursor->next;
    }
    return rc;
}

static int _print_dep(char* name, struct module** modules, int nb_modules, int show)
{
int rc = 0;
struct module* base;

    base = _lookup_module(name, modules, nb_modules);
    if(base)
    {
        _print_module(base, show, 0);
    }
    else
    {
        fprintf(stderr, "module:%s is not a known module\n", name);
        rc = 1;
    }
    return rc;
}

static void _usage(void)
{
   fprintf(stderr, "Usage: module_dep ( -c | --children | -p | --parent ) <list_of_build.lst_filename>\n");
}

int main(int argc, char** argv)
{
int rc = 0;
int i;
char* base_module_name = NULL;
int show = 0;
struct module** modules;
int nb_modules = 0;
int verbose = 0;

    /* we will have no more modules that there are arguments (in fact we should have 3 less than) */
    modules = calloc(argc, sizeof(struct module*));

    if(argc < 4)
    {
        _usage();
    }
    for (i = 1; i < argc; i++)
    {
        if(!strcmp(argv[i],"-h") || !strcmp(argv[i], "--help"))
        {
            _usage();
        }
        else if(!strcmp(argv[i],"-v"))
        {
            verbose = 1;
        }
        else if(!strcmp(argv[i],"-u") || !strcmp(argv[i], "--unique"))
        {
            show |= SHOW_F_UNIQUE;
        }
        else if(!strcmp(argv[i],"-p") || !strcmp(argv[i], "--parent"))
        {
            i += 1;
            if(i >= argc)
            {
                fprintf(stderr, "missing options' argument after %s\n", argv[i - 1]);
                exit(1);
            }
            if(base_module_name)
            {
                fprintf(stderr, "there can be only one -p or -c options specified\n");
                exit(1);
            }
            show |= SHOW_F_PARENTS;
            base_module_name = argv[i];
        }
        else if(!strcmp(argv[i],"-c") || !strcmp(argv[i], "--children"))
        {
            i += 1;
            if(i >= argc)
            {
                fprintf(stderr, "missing options' argument after %s\n", argv[i - 1]);
                exit(1);
            }
            if(base_module_name)
            {
                fprintf(stderr, "there can be only one -p or -c options specified\n");
                exit(1);
            }
            show |= SHOW_F_CHILDREN;
            base_module_name = argv[i];
        }
        else
        {
        struct module* module;

            module = _load_module_deps(argv[i], verbose);
            if(module)
            {
                modules[nb_modules++] = module;
            }
            else
            {
                exit(1);
            }
        }
    }
    if(base_module_name)
    {
        rc = _resolve_dep(modules, nb_modules);
        if(!rc)
        {
            rc = _print_dep(base_module_name, modules, nb_modules, show);
        }
    }
    else
    {
        fprintf(stderr, "there must be one -p or -c options specified\n");
        exit(1);
    }
    return rc;
}
