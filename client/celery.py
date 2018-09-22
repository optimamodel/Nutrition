#!/usr/bin/env python

import nutrition_app.apptasks as at

at.celery_instance.worker_main([__file__, '-l', 'info']) # Run Celery