FROM public.ecr.aws/lambda/python:3.12

# Copy function code
COPY lambda_function.py detect.py ${LAMBDA_TASK_ROOT}

# Install the function's dependencies
COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Set the CMD to your handler
CMD [ "lambda_function.lambda_handler" ]