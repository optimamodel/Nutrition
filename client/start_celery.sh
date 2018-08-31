#!/bin/bash
celery worker -A nutrition_app.apptasks -l info
