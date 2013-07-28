//
//  main.m
//  AXText
//
//  Created by Boris Dušek on 14.10.12.
//  Copyright (c) 2012 Boris Dušek. All rights reserved.
//
//This tool currently logs the AXAttributedString of the first AXTextArea
//found in LibreOffice (suited for Writer), and logs all AXValueChanged
//and AXSelectedTextChanged notifications of that AXTextArea and also all
//AXFocusedUIElementChange notifications. It can be adjusted to do
//the same thing for TextEdit so that one can learn from it
// how stuff should be implemented (TextEdit is basically
//*the* reference implementation of AXTextArea).
//
//Any adjustments (e.g. to observe TextEdit instead of LibreOffice)
//need to be done in the source code of this tool.

#import <ApplicationServices/ApplicationServices.h>
#import <Cocoa/Cocoa.h>

#define AX_CALL_(function, ...) if (kAXErrorSuccess != (err = function(__VA_ARGS__))) {\
NSLog(@"Failed AX Call %s with return value %d", #function, err);\
} else
#define AX_CALL(type, var, result_type, function, ...) \
type var;\
AX_CALL_(function, __VA_ARGS__, ((result_type *)&var))
#define AX_VALUE(element, type, var, attr) AX_CALL(type, var, CFTypeRef, AXUIElementCopyAttributeValue, (element), kAX##attr##Attribute)
#define AX_PVALUE(element, type, var, attr, parameter) AX_CALL(type, var, CFTypeRef, AXUIElementCopyParameterizedAttributeValue, element, kAX##attr##ParameterizedAttribute, parameter)
#define AX_CHILD(element, role, title, child) AX_CALL(AXUIElementRef, (child), AXUIElementRef, findChildOfRoleAndTitle, (element), kAX##role##Role, (title))
#define AX_APPLICATION(appname, appvar, callback, observer) AX_CALL(AXUIElementRef, appvar, AXUIElementRef, findApplication, appname, callback, observer)
#define AX_OBSERVE(observer, element, notification) AX_CALL_(AXObserverAddNotification, observer, element, kAX##notification##Notification, NULL)
#define AX_PARENT(child, parent) AX_VALUE(child, AXUIElementRef, parent, Parent)

static AXError findChildOfRoleAndTitle(AXUIElementRef element, CFStringRef role, NSString* title, AXUIElementRef *child)
{
    AXError err = kAXErrorSuccess;
    AX_VALUE(element, CFArrayRef, children, Children) {
        for (size_t i = 0; i < CFArrayGetCount(children); ++i) {
            AXUIElementRef candidate = CFArrayGetValueAtIndex(children, i);
            AX_VALUE(candidate, CFStringRef, actualRole, Role) {
                if (CFEqual(role, actualRole)) {
                    if (title) {
                        AX_VALUE(candidate, CFStringRef, actualTitle, Title) {
                            if (CFEqual((__bridge CFStringRef)title, actualTitle)) {
                                *child = candidate;
                                return err;
                            }
                        }
                    } else {
                        *child = candidate;
                        return err;
                    }
                }
            }
        }
    }
    err = kAXErrorFailure;
    return err;
}

static AXError findApplication(NSString *title, AXObserverCallback callback, AXObserverRef *observer, AXUIElementRef *application) {
    AXError err = kAXErrorSuccess;
    for (NSRunningApplication *app in [[NSWorkspace sharedWorkspace] runningApplications]) {
        if ([app.localizedName isEqualToString:title]) {
            *application = AXUIElementCreateApplication([app processIdentifier]);
            err = (*application) ? kAXErrorSuccess: kAXErrorFailure;
            if ((kAXErrorSuccess == err) && observer) {
                AX_CALL_(AXObserverCreate, [app processIdentifier], callback, observer) {
                    AX_OBSERVE(*observer, *application, FocusedUIElementChanged) {
                    }
                }
            }
            break;
        }
        err = kAXErrorFailure;
    }
    return err;
}



static void axLoggingObserverCallback(AXObserverRef observer, AXUIElementRef element, CFStringRef notification, void *refcon) {
    AXError err = kAXErrorSuccess;
    AX_VALUE(element, CFStringRef, role, Role) {
        NSLog(@"%@ (%@): %@", element, role, notification);
    }
}



static AXError findTextEditTextComponent(AXObserverCallback callback, AXObserverRef *observer, AXUIElementRef *component) {
    AXError err = kAXErrorSuccess;
    AX_APPLICATION(@"TextEdit", TextEdit, callback, observer) {
        AX_CHILD(TextEdit, Window, 0, window) {
            AX_CHILD(window, ScrollArea, 0, scrollArea) {
                AX_CHILD(scrollArea, TextArea, 0, textArea) {
                    *component = textArea;
                }
            }
        }
    }
    return err;
}

static AXError findTextMateTextComponent(AXObserverCallback callback, AXObserverRef *observer, AXUIElementRef *component) {
    AXError err = kAXErrorSuccess;
    AX_APPLICATION(@"TextMate", TextMate, callback, observer) {
        AX_CHILD(TextMate, Window, 0, window) {
            AX_CHILD(window, ScrollArea, 0, scrollArea) {
                AX_CHILD(scrollArea, TextArea, 0, textArea) {
                    *component = textArea;
                }
            }
        }
    }
    return err;
}

static AXError findLibreOfficeTextComponent(AXObserverCallback callback, AXObserverRef *observer, AXUIElementRef *component) {
    AXError err = kAXErrorSuccess;
    AX_APPLICATION(@"LibreOffice", LibreOffice, callback, observer) {
        AX_CHILD(LibreOffice, Window, 0, window) {
            AX_CHILD(window, ScrollArea, 0, scrollArea) {
                AX_CHILD(scrollArea, Group, 0, group) {
                    AX_CHILD(group, TextArea, 0, textArea) {
                        *component = textArea;
                    }
                }
            }
        }
    }
    return err;
}

static AXError reportOnAXTextArea(AXUIElementRef textArea) {
    AXError err = kAXErrorSuccess;
    AX_VALUE(textArea, CFNumberRef, length, NumberOfCharacters) {
        CFRange all = CFRangeMake(0, 0);
        CFNumberGetValue(length, kCFNumberCFIndexType, &all.length);
        AXValueRef allValue = AXValueCreate(kAXValueCFRangeType, &all);
        AX_PVALUE(textArea, CFAttributedStringRef, attrString, AttributedStringForRange, allValue) {
            NSLog(@"Attributed String = \"%@\"", attrString);
        }
    }
    return err;
}

static AXError reportOnAXTextArea_Bounds(AXUIElementRef textArea) {
    AXError err = kAXErrorSuccess;
    CFRange all = CFRangeMake(30, 6);
    AXValueRef allValue = AXValueCreate(kAXValueCFRangeType, &all);
    AX_PVALUE(textArea, CFAttributedStringRef, attrString, AttributedStringForRange, allValue) {
        NSLog(@"Attributed String = \"%@\"", attrString);
        AX_PVALUE(textArea, CFAttributedStringRef, bounds, BoundsForRange, allValue) {
            NSLog(@"Bounds = %@", bounds);
        }
    }
    return err;
}

static AXError registerTextNotifications(AXObserverRef observer, AXUIElementRef element) {
    AXError err = kAXErrorSuccess;
    AX_OBSERVE(observer, element, SelectedTextChanged) {
        AX_OBSERVE(observer, element, ValueChanged) {
        }
    }
    return err;
}

static AXError registerTextNotificationsCascade(AXObserverRef observer, AXUIElementRef element) {
    AXError err = kAXErrorSuccess;
    while (kAXErrorSuccess == err) {
        AX_CALL_(registerTextNotifications, observer, element) {
            AX_VALUE(element, CFStringRef, role, Role) {
                if (CFEqual(kAXApplicationRole, role)) {
                    break;
                }
                AX_PARENT(element, elementParent) {
                    element = elementParent;
                }
            }
        }
    }
    return err;
}


int main(int argc, char **argv)
{
    AXError err;
    AXUIElementRef textArea;
    AXObserverRef observer;
    AX_CALL_(findLibreOfficeTextComponent/*findTextEditTextComponent*/, axLoggingObserverCallback, &observer, &textArea) {
        AX_CALL_(reportOnAXTextArea, textArea) {
            AX_CALL_(registerTextNotifications, observer, textArea) {
                CFRunLoopSourceRef axNotificationSource = AXObserverGetRunLoopSource(observer);
                CFRunLoopRef runLoop = CFRunLoopGetMain();
                CFRunLoopAddSource(runLoop, axNotificationSource, kCFRunLoopDefaultMode);
                CFRunLoopRun();
            }
        }
    }
    return kAXErrorSuccess == err;
}