#get MySQL image
FROM mysql:9.0.1

# Set environment variables for MySQL configuration
ENV MYSQL_ROOT_PASSWORD=1234

#copy the billingdb.sql file into the container
COPY billingdb.sql ./docker-entrypoint-initdb.d

EXPOSE 3306