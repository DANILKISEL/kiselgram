FROM gradle:9.3.0-jdk21 AS build
WORKDIR /home/gradle/src
COPY . .
RUN gradle --no-daemon installDist

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /home/gradle/src/build/install/KiselgramJava/ /app/
EXPOSE 5000
CMD ["/app/bin/KiselgramJava"]
