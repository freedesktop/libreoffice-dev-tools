

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

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
    int gmake;
};

static int verbose;

#define SHOW_F_PARENTS  (int)(1<<0)
#define SHOW_F_CHILDREN (int)(1<<1)
#define SHOW_F_UNIQUE   (int)(1<<2)
#define SHOW_F_NO_GMAKE_MODULES (int)(1<<3)
#define SHOW_F_GRAPH (int)(1<<4)

const char* graph_boilerplate =
"digraph G {\n"
"node [shape=\"Mrecord\", color=\"#BBBBBB\"]\n"
" node  [fontname=Verdana, fontsize=10, height=0.02, width=0.02]\n"
" edge  [color=\"#31CEF0\", len=0.5]\n"
" edge  [fontname=Arial, fontsize=10, fontcolor=\"#31CEF0\"]\n"
    ;

static int _compare_module(struct module** a, struct module** b)
{
    return strcmp((*a)->name, (*b)->name);
}

static struct module* _load_module_deps(char* filename)
{
FILE* fp;
struct module* module = NULL;
char* children_start;
struct stat st;
char buffer[4096]; /* ok ugly, we should really be dynamic here... but that will do for now */
int gmake_module = 0;

    memset(&st, 0, sizeof(struct stat));
    if(stat(filename, &st))
    {
        fprintf(stderr, "error getting stat() on %s\n", filename);
        exit(1);
    }
    if(!S_ISDIR(st.st_mode))
    {
        fprintf(stderr, "%s is not a directory, skip\n", filename);
        return NULL;
    }
    sprintf(buffer, "%s/prj/d.lst", filename);
    if(!stat(buffer, &st))
    {
        if(S_ISREG(st.st_mode) && st.st_size < 2)
        {
            gmake_module = 1;
        }
    }

    sprintf(buffer, "%s/prj/build.lst", filename);
    fp = fopen(buffer, "r");
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
            module->gmake = gmake_module;
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
                module->list_parents = malloc(len + 1);
                memcpy(module->list_parents, children_start, len + 1);
            }
        }
        else
        {
            fprintf(stderr, "error reading %s\n", buffer);
            exit(1);
        }
        fclose(fp);
    }
    else
    {
        if(verbose)
        {
            fprintf(stderr, "skipping %s, probably not a module\n", filename);
        }
    }
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
            if(verbose)
            {
                fprintf(stderr, "parent for %s :|%s|\n", module->name, cursor);
            }

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
                    fprintf(stderr, "Error: dependency %s of module %s does not have a known build.lst associated to it\n", cursor, module->name);
                }
            }
            cursor += strlen(cursor) + 1;
        }
    }
    return rc;
}

static int is_subtree_gbuildified(struct module* module, int show)
{
    if(is_subtree_gbuildified)
    {
        if(verbose)
        {
            printf("=> is_subtree_gbuildified(%s)\n", module->name);
        }
    }
    struct module_ref* cursor = NULL;
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
        int rc = is_subtree_gbuildified(cursor->module, show);
        if (!rc)
        {
            if (verbose)
            {
                printf ("returns %d\n", rc);
            }
            return 0;
        }
        cursor = cursor->next;
    }

    int rc = module->gmake;
    if(verbose)
    {
        printf ("returns %d\n", rc);
    }
    return rc;
}

static int _print_module_data(struct module* module, int show, int level)
{
    int rc = 0;
    if (show & SHOW_F_GRAPH)
    {
        struct module_ref* visitor = NULL;
        if(show & SHOW_F_CHILDREN)
        {
            visitor = module->children;
        }
        if(show & SHOW_F_PARENTS)
        {
            visitor = module->parents;
        }
        if (!module->gmake)
        {
            rc += 1;
            printf ("\"%s\" [shape=box, color=deeppink]\n", module->name);
        }
        while(visitor)
        {
            if(show & SHOW_F_CHILDREN)
            {
                printf ("\"%s\" -> \"%s\"\n", visitor->module->name, module->name);
            }
            else
            {
                printf ("\"%s\" -> \"%s\"\n", module->name, visitor->module->name);
            }
            visitor = visitor->next;
        }
    }
    else
    {
        int i;
        for(i = 0; i < level - 1; i++)
        {
            printf("   ");
        }
        if(i < level)
        {
            if(module->gmake)
            {
                printf("  + %s (*)\n", module->name);
            }
            else
            {
                printf("  + %s\n", module->name);
                rc += 1;
            }
        }
        else
        {
            if(module->gmake)
            {
                printf("%s (*)\n", module->name);
            }
            else
            {
                printf("%s\n", module->name);
                rc += 1;
            }
        }
    }
    return rc;
}

static int _traverse_module(struct module* module, int show, int level)
{
struct module_ref* cursor = NULL;
int rc;

    if(show & SHOW_F_UNIQUE)
    {
        if(module->traversed)
        {
            return 0;
        }
        module->traversed = 1;
    }

    if(show & SHOW_F_NO_GMAKE_MODULES)
    {
        if (is_subtree_gbuildified(module, show))
        {
            module->traversed = 1;
            return 0;
        }
    }

    if(level > 512)
    {
        fprintf(stderr, "Error runaway recursion... recursive dependencies ?\n");
        exit(1);
    }

    rc = _print_module_data(module, show, level);

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
        rc += _traverse_module(cursor->module, show, level + 1);
        cursor = cursor->next;
    }
    return rc;
}

static int _print_dep(char* name, struct module** modules, int nb_modules, int show)
{
int rc = 0;
int nb_non_gmake = 0;
struct module* base;

    base = _lookup_module(name, modules, nb_modules);
    if(base)
    {
        if (show & SHOW_F_GRAPH)
        {
            printf("%s", graph_boilerplate);
        }
        nb_non_gmake = _traverse_module(base, show, 0);
        if (show & SHOW_F_GRAPH)
        {
            printf("\n}\n");
        }
        else
        {
            if(show & SHOW_F_CHILDREN)
            {
                printf("\n%d non gbuild children\n", nb_non_gmake);
            }
        }
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
   fprintf(stderr, "Usage: module_dep [options] (-c | --children | -p | --parent) module <list_of_build.lst_filename>\n");
   fprintf(stderr, "       where options are a combination of:\n");
   fprintf(stderr, "       --unique   | -u unique occurence of each module\n");
   fprintf(stderr, "       --suppress | -s suppress completely gbuildified subtrees\n");
   fprintf(stderr, "       --graph    | -g output graphviz dot file format\n\n");
   fprintf(stderr, "Sample 1: module_dep -u -c svx\n");
   fprintf(stderr, "Sample 2: module_dep -c svx -g | dot -Tpng -osvx.png\n");
   exit(1);
}

int main(int argc, char** argv)
{
int rc = 0;
int i;
char* base_module_name = NULL;
int show = 0;
struct module** modules;
int nb_modules = 0;

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
        else if(!strcmp(argv[i],"-s") || !strcmp(argv[i], "--suppress"))
        {
            show |= SHOW_F_NO_GMAKE_MODULES;
        }
        else if(!strcmp(argv[i],"-g") || !strcmp(argv[i], "--graph"))
        {
            show |= SHOW_F_UNIQUE;
            show |= SHOW_F_GRAPH;
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

            module = _load_module_deps(argv[i]);
            if(module)
            {
                modules[nb_modules++] = module;
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
