# Build Stage
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy the entire solution and project files first
COPY services/api_gateway/CvAssistant.ApiGateway.sln services/api_gateway/
COPY services/api_gateway/CvAssistant.ApiGateway.Domain/CvAssistant.ApiGateway.Domain.csproj services/api_gateway/CvAssistant.ApiGateway.Domain/
COPY services/api_gateway/CvAssistant.ApiGateway.Application/CvAssistant.ApiGateway.Application.csproj services/api_gateway/CvAssistant.ApiGateway.Application/
COPY services/api_gateway/CvAssistant.ApiGateway.Infrastructure/CvAssistant.ApiGateway.Infrastructure.csproj services/api_gateway/CvAssistant.ApiGateway.Infrastructure/
COPY services/api_gateway/CvAssistant.ApiGateway.API/CvAssistant.ApiGateway.API.csproj services/api_gateway/CvAssistant.ApiGateway.API/

# Restore dependencies
RUN dotnet restore services/api_gateway/CvAssistant.ApiGateway.sln

# Copy the rest of the source code
COPY services/api_gateway/ services/api_gateway/

WORKDIR /src/services/api_gateway/CvAssistant.ApiGateway.API
RUN dotnet publish -c Release -o /app/publish /p:UseAppHost=false

# Runtime Stage
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final
WORKDIR /app
COPY --from=build /app/publish .

EXPOSE 8081
ENTRYPOINT ["dotnet", "CvAssistant.ApiGateway.API.dll"]
