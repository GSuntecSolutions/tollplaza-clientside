# Machine B (Client machine / GPU m/c )
celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info  # 
celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info



# Machine A (GSTS machine / non GPU m/c ):
celery -A app.redis_que_sys.db_saver worker --loglevel=info
