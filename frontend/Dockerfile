# frontend/Dockerfile
# Build Stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# We proxy requests via nginx to backend on /api or /v1
RUN npm run build

# Serve Stage with Nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
# Setup Nginx to proxy API requests to the backend container
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
