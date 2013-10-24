/* Running trivial commands as builtin in GNU Make.
Copyright (C) 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997,
1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
2010 Free Software Foundation, Inc.
This file is part of GNU Make.

GNU Make is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

GNU Make is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.  */

#include "makeint.h"
#include "job.h"

#ifdef HAVE_DOS_PATHS
/* TODO: For some reason WINDOWS32 is not set when building on Cygwin,
   so enable the fast Windows builtins this way.
*/
#define MYWIN
#else
#define DISABLE /* don't bother otherwise */
#endif

#ifdef MYWIN
#include <windows.h>
#include <unistd.h>
#endif

#include <assert.h>
#include <stdio.h>
#include <string.h>

static int equals( const char* str1, const char* str2 )
{
    if( str1 == NULL || str2 == NULL )
        return 0;
    return strcmp( str1, str2 ) == 0;
}

/* Split a shell command into arguments.
   Based on construct_command_argv_internal(), with #ifdef ORIGINAL_CODE
   for modifications.
*/
static char** split_shell_args( char* line )
{
#ifndef ORIGINAL_CODE
  /* Disable some code that's not needed here. */
  const int unixy_shell = 0;
  const int oneshell = 0;
  char** restp = NULL;
#endif

  static char sh_chars_sh[]  = "#;\"*?[]&|<>(){}$`^";
  char** new_argv;
  char* ap;
  char* end;
  char* argstr;
  int i;
  char *p;
  int instring, word_has_equals, seen_nonequals, last_argument_was_empty;

  /* Make sure not to bother processing an empty line.  */
  while (isblank ((unsigned char)*line))
    ++line;
  if (*line == '\0')
    return 0;

  i = strlen (line) + 1;

  /* More than 1 arg per character is impossible.  */
  new_argv = xmalloc (i * sizeof (char *));

#ifdef ORIGINAL_CODE
  /* All the args can fit in a buffer as big as LINE is.   */
  ap = new_argv[0] = argstr = xmalloc (i);
  end = ap + i;
#else
  /* They actually need a bigger buffer, because we do variable expansion. */
  const int max_line_len = 64 * 1024;
  ap = new_argv[0] = argstr = xmalloc( max_line_len );
  end = ap + max_line_len;
#endif

  /* I is how many complete arguments have been found.  */
  i = 0;
  instring = word_has_equals = seen_nonequals = last_argument_was_empty = 0;
  for (p = line; *p != '\0'; ++p)
    {
      assert (ap <= end);

#ifndef ORIGINAL_CODE
      /* Expand variables from gb_Helper_abbreviate_dirs. They are one char long and
         are used for paths. Do not expand them inside single quotes. */
      if( instring != '\''
        && *p == '$' && isalpha( p[ 1 ] ) && ( p[ 2 ] == '/' || p[ 2 ] == ' ' ))
      {
        int j;
        for( j = 0;
             j < i;
             ++j )
        {
          if( new_argv[ j ][ 0 ] == p[ 1 ] && new_argv[ j ][ 1 ] == '=' )
          { /* Found var definition, expand. */
             ++p;
             const char* from = new_argv[ j ] + 2;
             while( *from != '\0' )
                *ap++ = *from++;
             break;
          }
        }
      }
#endif
      if (instring)
	{
	  /* Inside a string, just copy any char except a closing quote
	     or a backslash-newline combination.  */
	  if (*p == instring)
	    {
	      instring = 0;
	      if (ap == new_argv[0] || *(ap-1) == '\0')
		last_argument_was_empty = 1;
	    }
	  else if (*p == '\\' && p[1] == '\n')
            {
              /* Backslash-newline is handled differently depending on what
                 kind of string we're in: inside single-quoted strings you
                 keep them; in double-quoted strings they disappear.
	         For DOS/Windows/OS2, if we don't have a POSIX shell,
		 we keep the pre-POSIX behavior of removing the
		 backslash-newline.  */
              if (instring == '"'
#if defined (__MSDOS__) || defined (__EMX__) || defined (WINDOWS32)
		  || !unixy_shell
#endif
		  )
                ++p;
              else
                {
                  *(ap++) = *(p++);
                  *(ap++) = *p;
                }
            }
	  else if (*p == '\n' && restp != NULL)
	    {
	      /* End of the command line.  */
	      *restp = p;
	      goto end_of_line;
	    }
#ifdef ORIGINAL_CODE
	  /* Backslash, $, and ` are special inside double quotes.
	     If we see any of those, punt.
	     But on MSDOS, if we use COMMAND.COM, double and single
	     quotes have the same effect.  */
	  else if (instring == '"' && strchr ("\\$`", *p) != 0 && unixy_shell)
	    goto slow;
#endif
	  else
	    *ap++ = *p;
	}
#ifdef ORIGINAL_CODE
      else if (strchr (sh_chars, *p) != 0)
	/* Not inside a string, but it's a special char.  */
	goto slow;
      else if (one_shell && *p == '\n')
	/* In .ONESHELL mode \n is a separator like ; or && */
	goto slow;
#ifdef  __MSDOS__
      else if (*p == '.' && p[1] == '.' && p[2] == '.' && p[3] != '.')
	/* `...' is a wildcard in DJGPP.  */
	goto slow;
#endif
#endif
      else
	/* Not a special char.  */
	switch (*p)
	  {
	  case '=':
#ifdef ORIGINAL_CODE
	    /* Equals is a special character in leading words before the
	       first word with no equals sign in it.  This is not the case
	       with sh -k, but we never get here when using nonstandard
	       shell flags.  */
	    if (! seen_nonequals && unixy_shell)
	      goto slow;
#endif
	    word_has_equals = 1;
	    *ap++ = '=';
	    break;
	  case '\\':
	    /* Backslash-newline has special case handling, ref POSIX.
               We're in the fastpath, so emulate what the shell would do.  */
	    if (p[1] == '\n')
	      {
		/* Throw out the backslash and newline.  */
                ++p;

                /* If there's nothing in this argument yet, skip any
                   whitespace before the start of the next word.  */
                if (ap == new_argv[i])
                  p = next_token (p + 1) - 1;
	      }
	    else if (p[1] != '\0')
              {
#ifdef HAVE_DOS_PATHS
                /* Only remove backslashes before characters special to Unixy
                   shells.  All other backslashes are copied verbatim, since
                   they are probably DOS-style directory separators.  This
                   still leaves a small window for problems, but at least it
                   should work for the vast majority of naive users.  */

#ifdef __MSDOS__
                /* A dot is only special as part of the "..."
                   wildcard.  */
                if (strneq (p + 1, ".\\.\\.", 5))
                  {
                    *ap++ = '.';
                    *ap++ = '.';
                    p += 4;
                  }
                else
#endif
                  if (p[1] != '\\' && p[1] != '\''
                      && !isspace ((unsigned char)p[1])
                      && strchr (sh_chars_sh, p[1]) == 0)
                    /* back up one notch, to copy the backslash */
                    --p;
#endif  /* HAVE_DOS_PATHS */

                /* Copy and skip the following char.  */
                *ap++ = *++p;
              }
	    break;

	  case '\'':
	  case '"':
	    instring = *p;
	    break;

	  case '\n':
	    if (restp != NULL)
	      {
		/* End of the command line.  */
		*restp = p;
		goto end_of_line;
	      }
	    else
	      /* Newlines are not special.  */
	      *ap++ = '\n';
	    break;

	  case ' ':
	  case '\t':
	    /* We have the end of an argument.
	       Terminate the text of the argument.  */
	    *ap++ = '\0';
	    new_argv[++i] = ap;
	    last_argument_was_empty = 0;

#ifdef ORIGINAL_CODE
	    /* Update SEEN_NONEQUALS, which tells us if every word
	       heretofore has contained an `='.  */
	    seen_nonequals |= ! word_has_equals;
	    if (word_has_equals && ! seen_nonequals)
	      /* An `=' in a word before the first
		 word without one is magical.  */
	      goto slow;
#endif
	    word_has_equals = 0; /* Prepare for the next word.  */

#ifdef ORIGINAL_CODE
	    /* If this argument is the command name,
	       see if it is a built-in shell command.
	       If so, have the shell handle it.  */
	    if (i == 1)
	      {
		register int j;
		for (j = 0; sh_cmds[j] != 0; ++j)
                  {
                    if (streq (sh_cmds[j], new_argv[0]))
                      goto slow;
# ifdef __EMX__
                    /* Non-Unix shells are case insensitive.  */
                    if (!unixy_shell
                        && strcasecmp (sh_cmds[j], new_argv[0]) == 0)
                      goto slow;
# endif
                  }
	      }
#endif

	    /* Ignore multiple whitespace chars.  */
	    p = next_token (p) - 1;
	    break;

	  default:
	    *ap++ = *p;
	    break;
	  }
    }
 end_of_line:

  if (instring)
    /* Let the shell deal with an unterminated quote.  */
#ifdef ORIGINAL_CODE
    goto slow;
#else
    goto broken;
#endif

  /* Terminate the last argument and the argument list.  */

  *ap = '\0';
  if (new_argv[i][0] != '\0' || last_argument_was_empty)
    ++i;
  new_argv[i] = 0;

#ifdef ORIGINAL_CODE
  if (i == 1)
    {
      register int j;
      for (j = 0; sh_cmds[j] != 0; ++j)
	if (streq (sh_cmds[j], new_argv[0]))
	  goto slow;
    }
#endif

#ifndef ORIGINAL_CODE
  /* Remove all variable definitions from the args, since they have been expanded,
     and all commands that are builtin do not depend on them indirectly.*/
  {
    char* writepos = argstr;
    int readpos;
    int skipnext = 0;
    int new_i = 0;
    for( readpos = 0;
         readpos < i;
         ++readpos )
    {
        if( skipnext )
        {
            skipnext = 0;
            if( new_argv[ readpos ][ 0 ] == '&' && new_argv[ readpos ][ 1 ] == '&'
                && new_argv[ readpos ][ 2 ] == '\0' )
            {
                continue; /* skip the && following the variable definition */
            }
        }
        if( isalpha( new_argv[ readpos ][ 0 ] ) && new_argv[ readpos ][ 1 ] == '=' )
            skipnext = 1; /* skip this and possibly next */
        else
        {
            const char* from = new_argv[ readpos ];
            new_argv[ new_i ] = writepos;
            while( *from != '\0' )
                *writepos++ = *from++;
            *writepos++ = '\0';
            ++new_i;
        }
    }
    i = new_i;
    new_argv[ i ] = NULL;
  }
#endif
  if (new_argv[0] == 0)
    {
      /* Line was empty.  */
      free (argstr);
      free (new_argv);
      return 0;
    }

  return new_argv;

#ifndef ORIGINAL_CODE
broken:
  if (new_argv != 0)
    {
      /* Free the old argument list we were working on.  */
      free (argstr);
      free (new_argv);
    }
  return NULL;
#endif
}

/* Is normal cases ignore any backticks or expansions that we cannot handle
   and let the real shell take care of it. */
static int is_normal_argument( const char* item )
{
    return item != NULL && strchr( item, '`' ) == NULL && strchr( item, '$' ) == NULL;
}

static int touch_file( const char* file )
{
#ifdef MYWIN
    int ok = 0;
    HANDLE handle = CreateFile( file, GENERIC_WRITE, 0, NULL, OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL, NULL );
    if( handle != INVALID_HANDLE_VALUE )
    {
        FILETIME time;
        GetSystemTimeAsFileTime( &time );
        if( SetFileTime( handle, NULL, NULL, &time ))
            ok = 1;
        CloseHandle( handle );
    }
    return ok;
#else
    return 1;
#endif
}

static int mkdir_p( const char* dir )
{
#ifdef MYWIN
    return CreateDirectory( dir, NULL ) || GetLastError() == ERROR_ALREADY_EXISTS;
#else
    return 1;
#endif
}

static int echo_to_file( const char* file, const char* txt, int append_nl )
{
#ifdef MYWIN
    int ok = 0;
    HANDLE handle = CreateFile( file, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL, NULL );
    if( handle != INVALID_HANDLE_VALUE )
    {
        DWORD written;
        if( WriteFile( handle, txt, strlen( txt ), &written, NULL )
            && written == strlen( txt )
            && ( !append_nl
                || ( WriteFile( handle, "\n", 1, &written, NULL )
                    && written == 1 )))
        {
            ok = 1;
        }
    CloseHandle( handle );
    return ok;
    }
#else
    return 1;
#endif
}

int try_run_as_builtin( char** orig_argv )
{
#ifdef DISABLE
    return 0;
#endif
    char** argv = orig_argv;
    if( argv == NULL || argv[ 0 ] == NULL )
        return 0;
    int builtin = 0;

/*    fprintf( stderr, "C: \'%s\' \'%s\' \'%s\' \'%s\'\n", argv[ 0 ], argv[ 0 ] ? argv[ 1 ] : NULL,
        argv[ 0 ] && argv[ 1 ] ? argv[ 2 ] : NULL, argv[ 0 ] && argv[ 1 ] && argv[ 2 ] ? argv[ 3 ] : NULL );
*/
    /* touch <file> */
    if( equals( argv[ 0 ], "touch" )
        && argv[ 1 ] != NULL
        && argv[ 2 ] == NULL )
    {
        if( touch_file( argv[ 1 ] ))
            builtin = 1;
    }
    /* mkdir -p <dir> */
    else if( equals( argv[ 0 ], "mkdir" )
        && equals( argv[ 1 ], "-p" )
        && argv[ 2 ] != NULL
        && argv[ 3 ] == NULL )
    {
        if( mkdir_p( argv[ 2 ] ))
            builtin = 1;
    }
    /* cp <srcfile> <destfile> */
    /* cp -f <srcfile> <destfile> */
    /* cp [--remove-destination] --no-dereference --force --preserve=timestamps <srcfile> <destfile> */
    else if( equals( argv[ 0 ], "/usr/bin/cp" ) || equals( argv[ 0 ], "/bin/cp" ) || equals( argv[ 0 ], "cp" ))
    {
        if( argv[ 1 ] != NULL
            && argv[ 2 ] != NULL
            && argv[ 3 ] == NULL )
        {
#ifdef MYWIN
            const char* srcfile = argv[ 1 ];
            const char* destfile = argv[ 2 ];
            if( CopyFile( srcfile, destfile, 0 ))
                builtin = 1;
#else
            builtin = 1;
#endif
        } else if( equals( argv[ 1 ], "-f" )
            && argv[ 2 ] != NULL
            && argv[ 3 ] != NULL
            && argv[ 4 ] == NULL )
        {
#ifdef MYWIN
            const char* srcfile = argv[ 2 ];
            const char* destfile = argv[ 3 ];
            DeleteFile( destfile );
            if( CopyFile( srcfile, destfile, 0 ))
                builtin = 1;
#else
            builtin = 1;
#endif
        }
        else
        {
            int remove = 0;
            if( equals( argv[ 1 ], "--remove-destination" )) // may not be present
                remove = 1;
            if( equals( argv[ 1 + remove ], "--no-dereference" )
                && equals( argv[ 2 + remove ], "--force" )
                && equals( argv[ 3 + remove ], "--preserve=timestamps" )
                && argv[ 4 + remove ] != NULL
                && argv[ 5 + remove ] != NULL
                && argv[ 6 + remove ] == NULL )
            {
#ifdef MYWIN
                const char* srcfile = argv[ 4 + remove ];
                const char* destfile = argv[ 5 + remove ];
                struct stat st;
                if( remove )
                    DeleteFile( destfile );
                /* Do we ever actually copy symlinks this way? Handle --no-dereference.
                   Not sure if Windows can handle them, so use POSIX. */
                if( lstat( srcfile, &st ) == 0 && S_ISLNK( st.st_mode ))
                {
                    DeleteFile( destfile );
                    if( symlink( srcfile, destfile ) == 0 )
                        builtin = 1;
                }
                else
                {
                    if( CopyFile( srcfile, destfile, 0 ))
                        builtin = 1;
                }
#else
            builtin = 1;
#endif
            }
        }
    }
    /* make has decided to run the command using shell */
    else if( is_bourne_compatible_shell( argv[ 0 ] )
        && equals( argv[ 1 ], "-c" )
        && argv[ 2 ] != NULL && argv[ 2 ][ 0 ] != ' '
        && argv[ 3 ] == NULL )
    {
        argv = split_shell_args( orig_argv[ 2 ] );
/*        fprintf( stderr, "SH \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\' \'%s\'\n",
            argv ? argv[ 0 ] : NULL,
            argv && argv[ 0 ] ? argv[ 1 ] : NULL,
            argv && argv[ 0 ] && argv[ 1 ] ? argv[ 2 ] : NULL,
            argv && argv[ 0 ] && argv[ 1 ] && argv[ 2 ] ? argv[ 3 ] : NULL,
            argv && argv[ 0 ] && argv[ 1 ] && argv[ 2 ] && argv[ 3 ] ? argv[ 4 ] : NULL,
            argv && argv[ 0 ] && argv[ 1 ] && argv[ 2 ] && argv[ 3 ] && argv[ 4 ] ? argv[ 5 ] : NULL,
            argv && argv[ 0 ] && argv[ 1 ] && argv[ 2 ] && argv[ 3 ] && argv[ 4 ] && argv[ 5 ] ? argv[ 6 ] : NULL );
*/
        if( argv == NULL )
            ; /* possibly sh given empty command given, but let it process anyway, just in case */
        /* mkdir -p <dir> && echo <txt> > <file> */
        else if( equals( argv[ 0 ], "mkdir" )
            && equals( argv[ 1 ], "-p" )
            && is_normal_argument( argv[ 2 ] )
            && equals( argv[ 3 ], "&&" )
            && equals( argv[ 4 ], "echo" )
            && argv[ 5 ] != NULL
            && equals( argv[ 6 ], ">" )
            && is_normal_argument( argv[ 7 ] )
            && argv[ 8 ] == NULL )
        {
            if( mkdir_p( argv[ 2 ] ) && echo_to_file( argv[ 7 ], argv[ 5 ], 1 ))
                builtin = 1;
        }
        /* mkdir -p <dir> && touch <file> */
        else if( equals( argv[ 0 ], "mkdir" )
            && equals( argv[ 1 ], "-p" )
            && is_normal_argument( argv[ 2 ] )
            && equals( argv[ 3 ], "&&" )
            && equals( argv[ 4 ], "touch" )
            && is_normal_argument( argv[ 5 ] )
            && argv[ 6 ] == NULL )
        {
            if( mkdir_p( argv[ 2 ] ) && touch_file( argv[ 5 ] ))
                builtin = 1;
        }
        /* mkdir -p `dirname <file>` && touch <file> */
        else if( equals( argv[ 0 ], "mkdir" )
            && equals( argv[ 1 ], "-p" )
            && equals( argv[ 2 ], "`dirname" )
            && argv[ 3 ][ strlen( argv[ 3 ] ) - 1 ] == '`'
            && equals( argv[ 4 ], "&&" )
            && equals( argv[ 5 ], "touch" )
            && is_normal_argument( argv[ 6 ] )
            && argv[ 7 ] == NULL )
        {
            // do the dirname first
            char* dir = strdup( argv[ 3 ] );
            dir[ strlen( dir ) - 1 ] = '\0'; // remove `
            if( is_normal_argument( dir ) && *dir != '\0' )
            {
                char* pos = dir + strlen( dir ) - 1;
                while( *pos != '/' && *pos != '\\' && pos > dir )
                    --pos;
                if( pos > dir )
                {
                    *pos = '\0';
                    if( mkdir_p( dir ) && touch_file( argv[ 6 ] ))
                        builtin = 1;
                }
            }
            free( dir );
        }
        if( argv != NULL )
        {
            free( argv[ 0 ] );
            free( argv );
        }
        argv = orig_argv;
    }
    return builtin;
}
