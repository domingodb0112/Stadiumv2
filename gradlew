#!/bin/sh
#
# Copyright © 2015-2021 the original authors.
#
# Gradle start up script for UN*X
#

APP_HOME=$(cd "$(dirname "$0")" && pwd)
APP_NAME="Gradle"
APP_BASE_NAME=$(basename "$0")

# Resolve JAVA_HOME
if [ -n "$JAVA_HOME" ] ; then
    if [ -x "$JAVA_HOME/jre/sh/java" ] ; then
        JAVACMD="$JAVA_HOME/jre/sh/java"
    else
        JAVACMD="$JAVA_HOME/bin/java"
    fi
    if [ ! -x "$JAVACMD" ] ; then
        die "JAVA_HOME is set to an invalid directory: $JAVA_HOME"
    fi
else
    JAVACMD="java"
fi

# Use gradle wrapper jar if present
WRAPPER_JAR="$APP_HOME/gradle/wrapper/gradle-wrapper.jar"
WRAPPER_PROPERTIES="$APP_HOME/gradle/wrapper/gradle-wrapper.properties"

exec "$JAVACMD" \
    -classpath "$WRAPPER_JAR" \
    "-Dorg.gradle.appname=$APP_BASE_NAME" \
    org.gradle.wrapper.GradleWrapperMain \
    "$@"
