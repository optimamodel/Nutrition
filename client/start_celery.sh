#!/bin/bash
celery worker -A nutrition_webapp.apptasks -l info
