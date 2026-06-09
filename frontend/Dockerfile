FROM node:20-trixie-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx ng build --configuration production

EXPOSE 4200

CMD ["sh","start.sh"]
