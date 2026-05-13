/*
 * Fluster - testing framework for decoders conformance
 * Copyright (C) 2025, Fluendo, S.A.
 *
 * Compatibility header for macOS
 * malloc.h doesn't exist on macOS - redirect to stdlib.h
 */

#ifndef _COMPAT_MALLOC_H
#define _COMPAT_MALLOC_H

#include <stdlib.h>

#endif /* _COMPAT_MALLOC_H */
