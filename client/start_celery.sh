#!/bin/bash
celery worker -A nutrition.webapp.apptasks -l info
