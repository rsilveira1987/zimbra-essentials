#!/opt/zimbra/bin/zmpython

"""
Script para atualizar a assinatura das contas zimbra de um determinado dominio em um determinado mailbox
"""

import urllib2
import logging
from com.zimbra.cs.account import Provisioning
from com.zimbra.cs.account import SearchAccountsOptions

########################################################################
# CONSTANTES
########################################################################
API_ADDRESS = '<endereco_http_da_api>'
DOMAIN = '<dominio_zimbra>'
DEFAULT_SIGNATURE_NAME = 'Assinatura Corporativa'
LOG_FILE = '/var/log/rotinas/zmsignature.log'
"""
LOG LEVELS:
logging.CRITICAL
logging.ERROR
logging.WARNING
logging.INFO
logging.DEBUG
logging.NOTSET
"""
LOG_LEVEL = logging.INFO


########################################################################
# Configurando o logging
########################################################################
# CRITICAL
# ERROR
# WARNING
# INFO
# DEBUG
# NOTSET
logging.basicConfig(
    level=LOG_LEVEL,
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

########################################################################
# Script principal
########################################################################
logging.debug('[Inicianco sincronizacao]')
prov = Provisioning.getInstance()
server = prov.getLocalServer()
domain = prov.getDomainByName(DOMAIN)
optionsDomain = SearchAccountsOptions(domain)
localAccts = prov.searchAccountsOnServer(server, optionsDomain)

logging.debug('[Iterando contas locais]')
# percorre a lista de contas do servidor
for acct in localAccts:

    # variavel para controlar a atualizacao da assinatura
    needToUpdate = False

    # somente contas de usuarios
    if acct.isIsSystemAccount():
        logging.warning("[%s] [SKIP] - Conta de sistema", acct.name)
        continue

    if acct.isIsExternalVirtualAccount():
        logging.warning("[%s] [SKIP] - Conta virtual",acct.name)
        continue

    if acct.isIsSystemResource():
        logging.warning("[%s] [SKIP] - Conta de recurso",acct.name)
        continue

    # obtem a assinatura no endpoint da API
    url = API_ADDRESS + "?user=" + acct.name

    try:

        # log
        logging.debug("[%s] [GET] - API", acct.name)

        # log
        logging.debug("[%s] [URL] - %s", acct.name,url)

        # realiza um GET para o endpoint da API
        response = urllib2.urlopen(url)

    except Exception,e:

        # log
        logging.debug("[%s] [ERROR] - %s",acct.name,str(e))
        logging.warning("[%s] [NOOP] - Assinatura nao encontrada",acct.name)

        # Output
        #print "ERROR: %s" % user

        continue

    # armazena o html da assinatura recebido
    html = response.read()

    # obtem todas as assinaturas do usuario
    allSignatures = acct.getAllSignatures()

    #
    # TODO: verifica se precisa atualizar?
    #

    # 1. Verifica se o usuario possui mais de uma assinatura
    if (not needToUpdate):
        if len(allSignatures) != 1:
            # log
            logging.info("[%s] [UPDATE] - Assinatura diferente de 1",acct.name)

            # Numero de assinaturas diferente de um (1), precisa atualizar
            needToUpdate = True



    # 2. Verifica se o usuario possui assinatura padrao
    if (not needToUpdate):
        # obtem a assinatura padrao
        defaultSignature = acct.getSignatureByName(DEFAULT_SIGNATURE_NAME)

        if defaultSignature is None:
            # log
            logging.info("[%s] [UPDATE] - Assinatura nao encontrada",acct.name)

            # Assinatura padrao nao encontrada
            needToUpdate = True

    # 3. Compara o conteudo das assinaturas
    if (not needToUpdate):
        # obtem a assinatura padrao
        defaultSignature = acct.getSignatureByName(DEFAULT_SIGNATURE_NAME)

        localContent = defaultSignature.getAttr('zimbraPrefMailSignatureHTML')

        if localContent != html:
            # log
            logging.info("[%s] [UPDATE] - Conteudo diferente",acct.name)

            # Conteudo das assinaturas esta diferente
            needToUpdate = True

    if needToUpdate:

        # log
        logging.info("[%s] [UPDATE] - Atualizando assinatura",acct.name)

        # remove todas as assinaturas da conta
        for s in allSignatures:
            acct.deleteSignature(s.id)

        # dados da assinatura
        data = {'zimbraPrefMailSignatureHTML':html}

        # cria a assinatura e define como padrao
        s = acct.createSignature(DEFAULT_SIGNATURE_NAME,data)
        acct.setPrefDefaultSignatureId(s.id)
        acct.setPrefForwardReplySignatureId(s.id)

        # Output
        # print "OK: %s" % user

    else:

        # log
        logging.info("[%s] [NOOP] - Nada a ser feito", acct.name)

logging.debug('[Fim sincronizacao]')




