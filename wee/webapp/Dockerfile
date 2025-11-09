# ตัวอย่างสำหรับ React/Angular/Vue หรือ static site
FROM node:18-alpine AS build
WORKDIR /app
COPY . .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=build /app/dist /webapp
