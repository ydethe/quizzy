#! /bin/bash

uv export --no-editable --no-emit-project -o requirements.txt > /dev/null
rm -rf dist && uv build
sudo docker build -t ydethe/quizzy .
sudo docker run -p 8030:8030 -v ./quizzes:/app/quizzes:ro ydethe/quizzy
# sudo docker push ydethe/quizzy
