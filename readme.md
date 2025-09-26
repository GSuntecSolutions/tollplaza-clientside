# Machine B (Client machine / GPU m/c )
celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info  # 
celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info



# Machine A (GSTS machine / non GPU m/c ):
celery -A app.redis_que_sys.db_saver worker --loglevel=info


V1 : Architecture is frame extration at GSTS end and procesing ie video gen and extract detail from image is at Client end 
and db is at GSTS and images and videos at client end. 

V2 : only frontend and db at GSTs m/c and all process is at teh client end 
