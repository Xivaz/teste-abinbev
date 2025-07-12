# Criação do Service Principal
# Este script cria um Service Principal no Azure e exibe as credenciais necessárias.
#!/bin/bash
set -e  # Habilita o modo de falha imediata
# Verifica se o Azure CLI está instalado
if ! command -v az &> /dev/null; then
    echo "Azure CLI não está instalado. Por favor, instale o Azure CLI para continuar."
    exit 1
fi
# Verifica se o usuário está autenticado no Azure
if ! az account show &> /dev/null; then
    echo "Você não está autenticado no Azure. Por favor, execute 'az login' para autenticar."
    exit 1
fi
# Cria o Service Principal
echo "Criando Service Principal..."
sp_name="AirflowServicePrincipal"
sp=$(az ad sp create-for-rbac --name "$sp_name" --role Contributor --scopes /subscriptions/$(az account show --query id -o tsv) --query "{
    appId: appId,
    password: password,
    tenant: tenant
}" -o json)
# Verifica se a criação foi bem-sucedida
if [ $? -ne 0 ]; then
    echo "Erro ao criar o Service Principal. Verifique suas permissões e tente novamente."
    exit 1
fi
# Exibe as credenciais do Service Principal
echo "Service Principal criado com sucesso!"
echo "Credenciais do Service Principal:"
echo "App ID: $(echo $sp | jq -r '.appId')"
echo "Password: $(echo $sp | jq -r '.password')"
echo "Tenant ID: $(echo $sp | jq -r '.tenant')"
echo "Certifique-se de armazenar essas credenciais em um local seguro, pois elas não serão exibidas novamente."
echo "Você pode usar essas credenciais para configurar o Airflow com autenticação baseada em Service Principal."
echo "Para mais informações, consulte a documentação do Azure sobre Service Principals."
# Fim do script
echo "Script concluído com sucesso."
exit 0
# Certifique-se de que o jq está instalado para manipulação de JSON
if ! command -v jq &> /dev/null; then
    echo "jq não está instalado. Por favor, instale o jq para manipulação de JSON."
    exit 1
fi
# Verifica se o usuário tem permissões suficientes para criar um Service Principal
if ! az role assignment list --assignee $(az account show --query user.name -o tsv) --query "[?roleDefinitionName=='Owner' || roleDefinitionName=='Contributor']" -o json | jq -e '. | length > 0' &> /dev/null; then
    echo "Você não tem permissões suficientes para criar um Service Principal. Por favor, solicite ao administrador as permissões necessárias."
    exit 1
fi
# Verifica se o usuário está na assinatura correta
subscription_id=$(az account show --query id -o tsv)
if [ -z "$subscription_id" ]; then
    echo "Não foi possível determinar a assinatura atual. Por favor, verifique sua configuração do Azure CLI."
    exit 1
fi
echo "Assinatura atual: $subscription_id"
# Finaliza o script com sucesso
echo "Tudo pronto! Você pode agora usar o Service Principal criado para autenticar suas aplicações no Azure."
echo "Obrigado por usar este script para criar um Service Principal!"