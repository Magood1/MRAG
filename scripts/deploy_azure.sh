#!/bin/bash

# --- Configuration ---
RESOURCE_GROUP="MRAG-Production-RG"
LOCATION="westeurope"
ACR_NAME="mragregistry$RANDOM" # Unique Name
APP_NAME="mrag-api-service-$RANDOM"
VAULT_NAME="mrag-kv-$RANDOM"
PLAN_NAME="mrag-plan"

# الألوان للمخرجات
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting MRAG Production Deployment...${NC}"

# التحقق من تسجيل الدخول
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Please login first: az login"
    exit 1
fi

# 1. إنشاء Resource Group (Idempotent check)
if [ $(az group exists --name $RESOURCE_GROUP) = false ]; then
    echo "Creating Resource Group: $RESOURCE_GROUP..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
else
    echo "Resource Group $RESOURCE_GROUP already exists."
fi

# 2. إنشاء ACR وبناء الصورة
echo "Setting up ACR..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true > /dev/null 2>&1
az acr login --name $ACR_NAME

ACR_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
echo "Building & Pushing Docker Image to $ACR_SERVER..."
docker build -t $ACR_SERVER/mrag-service:v1 .
docker push $ACR_SERVER/mrag-service:v1

# 3. إنشاء Key Vault وتخزين الأسرار
echo "Setting up Key Vault: $VAULT_NAME..."
az keyvault create --name $VAULT_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --sku standard > /dev/null 2>&1

echo "Storing Secrets..."
# ملاحظة: يفترض أن المتغير GEMINI_API_KEY موجود في بيئتك المحلية
az keyvault secret set --vault-name $VAULT_NAME --name "GeminiApiKey" --value "$GEMINI_API_KEY" > /dev/null

# 4. إنشاء Application Insights
echo "Creating Application Insights..."
az monitor app-insights component create --app $APP_NAME --location $LOCATION --kind web --resource-group $RESOURCE_GROUP --application-type web > /dev/null 2>&1
INSTRUMENTATION_KEY=$(az monitor app-insights component show --app $APP_NAME --resource-group $RESOURCE_GROUP --query connectionString --output tsv)

# 5. إنشاء App Service مع Managed Identity
echo "Creating App Service Plan & Web App..."
az appservice plan create --name $PLAN_NAME --resource-group $RESOURCE_GROUP --sku B1 --is-linux > /dev/null 2>&1

az webapp create --resource-group $RESOURCE_GROUP --plan $PLAN_NAME --name $APP_NAME --deployment-container-image-name "$ACR_SERVER/mrag-service:v1" --assign-identity "[system]" > /dev/null 2>&1

# 6. ربط الصلاحيات (Managed Identity -> Key Vault)
echo "Assigning Key Vault Access Policy..."
PRINCIPAL_ID=$(az webapp identity show --name $APP_NAME --resource-group $RESOURCE_GROUP --query principalId --output tsv)

az keyvault set-policy --name $VAULT_NAME --object-id $PRINCIPAL_ID --secret-permissions get list > /dev/null

# 7. تكوين التطبيق (Config Injection)
echo "Configuring App Settings..."
# نحتاج لبيانات اعتماد ACR لسحب الصورة (يمكن استخدام Managed Identity هنا أيضاً لـ ACR لكن سنبسطها الآن)
ACR_USER=$(az acr credential show --name $ACR_NAME --query "username" -output tsv)
ACR_PASS=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -output tsv)

az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings \
  ENVIRONMENT="production" \
  KEY_VAULT_NAME="$VAULT_NAME" \
  APPLICATIONINSIGHTS_CONNECTION_STRING="$INSTRUMENTATION_KEY" \
  DOCKER_REGISTRY_SERVER_URL="https://$ACR_SERVER" \
  DOCKER_REGISTRY_SERVER_USERNAME="$ACR_USER" \
  DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASS" \
  WEBSITES_PORT=8000 > /dev/null 2>&1

echo -e "${GREEN}✅ Deployment Complete!${NC}"
APP_URL="https://$APP_NAME.azurewebsites.net"
echo "App URL: $APP_URL"

# 8. Smoke Test
echo "Running Smoke Test..."
sleep 20 # انتظار بدء الحاوية
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" $APP_URL/health)
if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "${GREEN}Smoke Test Passed: Service is UP (200 OK)${NC}"
else
    echo "Smoke Test Failed: Status $HTTP_STATUS"
    echo "Check Logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

