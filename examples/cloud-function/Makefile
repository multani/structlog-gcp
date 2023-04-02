deploy:
	gcloud functions deploy test-log \
	--gen2 \
	--region europe-west1 \
	--runtime python310 \
	--source . \
	--entry-point test_func1 \
	--trigger-http
