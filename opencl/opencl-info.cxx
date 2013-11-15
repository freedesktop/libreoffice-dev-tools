/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include "clew.h"

#if defined(WIN32) | defined(_WIN32) || defined(__WIN32)
#include <Windows.h>
#define OPENCL_DLL_NAME "OpenCL.dll"
#elif defined(MACOSX)
#define OPENCL_DLL_NAME NULL
#else
#define OPENCL_DLL_NAME "libOpenCL.so"
#endif

#include <iostream>
#include <fstream>
#include <string>
#include <vector>

const size_t PLATFORM_INFO_SIZE = 512;
const size_t DEVICE_INFO_SIZE = 512;

void log_device(std::ofstream& file, cl_device_id id)
{
    char name[DEVICE_INFO_SIZE];
    cl_int state = clGetDeviceInfo(id, CL_DEVICE_NAME, DEVICE_INFO_SIZE, name, NULL);
    if(state != CL_SUCCESS)
        return;

    file << std::endl << "  OpenCL device" << std::endl;
    file << "   Name: " << name << std::endl;

    char version[DEVICE_INFO_SIZE];
    state = clGetDeviceInfo(id, CL_DEVICE_VERSION, DEVICE_INFO_SIZE, version, NULL);
    if(state != CL_SUCCESS)
        return;

    file << "   Version: " << version << std::endl;

    char vendor[DEVICE_INFO_SIZE];
    state = clGetDeviceInfo(id, CL_DEVICE_VENDOR, DEVICE_INFO_SIZE, vendor, NULL);
    if(state != CL_SUCCESS)
        return;

    file << "   Vendor: " << vendor << std::endl;

    cl_uint compute_units;
    state = clGetDeviceInfo(id, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(compute_units), &compute_units, NULL);
    if(state != CL_SUCCESS)
        return;

    file << "   Compute Units: " << compute_units << std::endl;

    char driver[DEVICE_INFO_SIZE];
    state = clGetDeviceInfo(id, CL_DRIVER_VERSION, DEVICE_INFO_SIZE, driver, NULL);
    if(state != CL_SUCCESS)
        return;

    file << "   Driver: " << driver << std::endl;

    char extensions[DEVICE_INFO_SIZE];
    state = clGetDeviceInfo(id, CL_DEVICE_EXTENSIONS, DEVICE_INFO_SIZE, extensions, NULL);
    if(state != CL_SUCCESS)
        return;

    file << "   Extensions: " << extensions << std::endl;
}

void log_platform(std::ofstream& file, cl_platform_id id)
{
    char name[PLATFORM_INFO_SIZE];
    cl_int state = clGetPlatformInfo(id, CL_PLATFORM_NAME, PLATFORM_INFO_SIZE, name, NULL);
    if(state != CL_SUCCESS)
        return;

    file << "OpenCL platform" << std::endl;
    file << "Name: " << name << std::endl;

    char vendor[PLATFORM_INFO_SIZE];
    state = clGetPlatformInfo(id, CL_PLATFORM_VENDOR, PLATFORM_INFO_SIZE, vendor, NULL);
    if(state != CL_SUCCESS)
        return;
    file << "Vendor: " << vendor << std::endl;

    char version[PLATFORM_INFO_SIZE];
    state = clGetPlatformInfo(id, CL_PLATFORM_VERSION, PLATFORM_INFO_SIZE, version, NULL);
    if(state != CL_SUCCESS)
        return;
    file << "OpenCL version: " << version << std::endl;

    char extensions[PLATFORM_INFO_SIZE];
    state = clGetPlatformInfo(id, CL_PLATFORM_EXTENSIONS, PLATFORM_INFO_SIZE, extensions, NULL);
    if(state != CL_SUCCESS)
        return;
    file << "Extensions: " << extensions << std::endl;

    cl_uint devices;
    state = clGetDeviceIDs(id, CL_DEVICE_TYPE_ALL, 0, NULL, &devices);
    if(state != CL_SUCCESS)
        return;

    std::vector<cl_device_id> deviceIDs(devices);
    state = clGetDeviceIDs(id, CL_DEVICE_TYPE_ALL, devices, &deviceIDs[0], NULL);
    if(state != CL_SUCCESS)
        return;

    for(size_t i = 0; i < devices; ++i)
    {
        log_device(file, deviceIDs[i]);
        file << std::endl;
    }
    file << std::endl;
}

void list_platforms(std::ofstream& file)
{
    cl_uint platforms;
    cl_int state = clGetPlatformIDs(0, NULL, &platforms);
    if(state != CL_SUCCESS)
        return;

    std::vector<cl_platform_id> platformIDs(platforms);
    state = clGetPlatformIDs(platforms, &platformIDs[0], NULL);
    if(state != CL_SUCCESS)
        return;

    for(size_t i = 0; i < platforms; ++i)
    {
        log_platform(file, platformIDs[i]);
    }
}

int main(int, char**)
{
    int status = clewInit(OPENCL_DLL_NAME);
    std::ofstream file("opencl.log");
    if(status < 0)
    {
        file << "failed to init OpenCL" << std::endl;
        return 1;
    }

    list_platforms(file);

    file << "success" << std::endl;
    return 0;
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
