# GeraLetra - MVP
# ----------------
# DESCRIÇÃO
#A partir de uma URL do Youtube retorna a letra que está no audio do vídeo, no formato específico para letras de música, ou texto corrido, caso seja um discurso, diálogo ou narração. O resultado pode ser copiado para a área de transferência.
# Se for uma música, o texto é formatado em versos e estrofes, com o refrão separado por linhas em branco. Se for um discurso, diálogo ou narração, o texto é organizado em parágrafos de acordo com a norma culta, quebrando o texto sempre que houver uma mudança de tópico, ideia ou interlocutor. O sistema não altera, não adiciona e não remove nenhuma palavra do texto original, apenas pontua e formata o layout.
# se for um vídeo, retorna um texto corrido
#Pipeline de IAs: Whisper para converter o áudio em texto e Gemini para formatar o texto de acordo com o que ele é: Texto corrido ou letra de música. O modelo do Gemini escolhido é o Gemini-2.5-flash, que é gratuito. O GPT-4 é pago, então não foi possível utilizar nessa versão MVP.


# MVP: Geração simples, dada a URL, retorna a letra formatada, 
# com opção de colocar o resultado na área de transferência

# Configurando as Bibliotecas...

#urlparse -- Manipula dados de um URL
from urllib.parse import parse_qs, urlparse

#sys
from email.mime import audio
import sys

#OS para poder manipular arquivos e diretórios
import os

# DOTENV para manipular o arquivo de configuração de variáveis de ambiente

#IMPORTANTE: O arquivo de configuração deve ser criado na raiz do projeto (arquivo .py), 
# .env apenas, sem nada antes do ponto, é o padrão para poder ser lido pelo "load_dotenv()". 

from dotenv import load_dotenv

load_dotenv()
api_key_gemini = os.getenv('GEMINI_API_KEY')
api_key_youtube = os.getenv('YOUTUBE_API_KEY')


#YOUTUBE
from googleapiclient.discovery import build

#Biblioteca para baixar o vídeo do YouTube e extrair o áudio
import yt_dlp

# Whisper para converter o áudio em texto
import whisper

#isodate -- Manipula dados de duração no formato ISO 8601
import isodate

#Gemini -- Para formatar o texto de acordo com o que ele é: Texto corrido ou letra de música
#OBS.: Foi a escolha pois é gratuito. O GPT-4 é pago

from google import genai

#pyperclip para copiar o resultado para a área de transferência
import pyperclip


################################################################################
# PASSO 1: Recebendo a URL do Usuário
#   Solicita a entrada de uma URL ao usuário e efetuar as devidas validações
################################################################################

#Iniciando a funcionalidade...
print ("Seja bem-vinda (o) ao GeraLetra! Vamos começar! \n")

urlvideo = input ("Informe o link de um vídeo do YouTube para extrair o texto do áudio: \n")

# Entrada não deve ser vazia
while len(urlvideo) == 0:
  print ("Nada foi informado e a entrada está vazia! \n")
  urlvideo = input ( "Para continuar, informe o link de um vídeo do YouTube: \n")

#Entrada deve ser uma URL do YouTube
#Retornando as informações da URL
resultado = urlparse(urlvideo)

#Lendo os atributos do que foi informado e fazendo as devidas validações
eh_url = resultado.scheme in ['http', 'https']
eh_url_youtube = resultado.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be']

#Se a string informada não é uma URL, a rotina é encerrada
if not eh_url:
    print ("O texto informado não é um link. Por favor, reinicie para tentar novamente!")
    exit() 

#Se a string informada não é uma URL do YouTube, a rotina é encerrada
elif not eh_url_youtube:
    print ("O texto informado é um link, porém não é do YouTube. Por favor, reinicie para tentar novamente!")
    exit() 

# A string é uma URL válida do YouTube. Vamos continuar para o Passo 2

################################################################################
## PASSO 2 - Validando o tamanho do Vídeo
#  Dada a URL válida, observar os metatados e verificar a duração do arquivo
################################################################################

#Checar nos metadados do video da URL qual a sua duração

#Extraindo o ID do Vídeo a partir da URL 

#Primeiro, precisamos saber se a URL é a longa ou a curta
eh_url_curta = resultado.netloc == 'youtu.be'

if eh_url_curta: #Quando URL curta, o ID do vídeo está no path
  id_video = resultado.path.lstrip('/')
else:
  dic_id_video = parse_qs(resultado.query)
  id_video = dic_id_video ['v'] [0]

#inicializando o objeto YouTube
youtube = build('youtube', 'v3', developerKey=api_key_youtube)

#Verificando nos metadados do video qual a  sua duração
metadados_video = youtube.videos().list(
    part='contentDetails',
    id=id_video).execute()

#Se os metadados do vídeo não retornarem nenhum resultado, significa que o vídeo é inválido ou não existe, e a rotina é encerrada.
if not metadados_video ['items']:
  print ("Não foi possível encontrar o vídeo a partir da URL informada. Por favor, reinicie para tentar novamente!")
  exit()

duracao_iso = metadados_video['items'][0]['contentDetails']['duration']

#Se a duração é ZERO, o vídeo é inválido e a rotina é encerrada
if duracao_iso == 'PT0S':
  print ("O vídeo encontrado tem duração ZERO ou é AO VIVO, o que é inválido. Por favor, reinicie para tentar novamente!")
  exit()  

#Extraindo a duração em segundos para validar se é menor do que 10 minutos

# REGRA DA API: A duração é retornada no formato ISO 8601: 
# Period Time 1Hour 2Minutes 30Seconds
# É preciso converter para segundos para validar a regra de negócio

duracao_segundos = isodate.parse_duration(duracao_iso).total_seconds()

#Como vem em segundos, precisamos converter para minutos para validar 
# a regra de negócio
duracao_minutos = duracao_segundos / 60

if duracao_minutos > 10:
  print ("O vídeo encontrado tem duração maior do que 10 minutos, o que é inválido. Por favor, reinicie para tentar novamente!")
  exit()

################################################################################
# PASSO 3 - Extraindo o arquivo mp3 do Video do YouTube
# DESCRIÇÃO:
# A partir da URL válida, de um vídeo de até 10 minutos de duração, 
# salvar TEMPORARIAMENTE o audio em um formato válido para a extração do texto
################################################################################

### Configurando a pasta e o arquivo temporário para salvar o áudio

# Cria a pasta 'temp' se ela não existir
os.makedirs('temp_geraletra', exist_ok=True)

#Define o nome do arquivo temporário para salvar o áudio
# OBS.: São 2 nomes pois o a API do Youtube coloca uma terminação diferente no arquivo baixado,
# e o tradutor para mp3 inclui a terminação .mp3. Assim, o arquivo fica com .mp3.mp3
#  e isso estava dando erro no Whisper. 

# Então, foi preciso diferenciar um do outro, da seguinte forma
# 1) Para Download: não é passada extensão alguma
# 2) Para o Whisper tem a extensão .mp3

#1) Download: temp_geraletra/audio_temp_idvideo.mp3
nome_arquivo_download = f'temp_geraletra/audio_temp_{id_video}'

#2) Para o Whisper
nome_arquivo_audio = f'temp_geraletra/audio_temp_{id_video}.mp3'


#### Baixando o vídeo do YouTube e salvando em arquivo
youtube_dl = yt_dlp.YoutubeDL()

# Definindoa as configurações (O dicionário de opções)

#OBS.: Quiet: True para não exibir mensagens de download, 
# progresso ou erros na tela, deixando a experiência do usuário mais limpa

opcoes = {
    'format': 'bestaudio/best',
    'outtmpl': nome_arquivo_download,
    'noplaylist': True,
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
}
with yt_dlp.YoutubeDL(opcoes) as ydl:
    ydl.download([urlvideo])

print ("[GeraLetra] Áudio extraído e salvo temporariamente com sucesso! Seguindo com a conversão para texto...\n")

################################################################################
# PASSO 4 - Executando a conversão em texto a partir do audio
# Com o arquivo de audio baixado, usar o Whisper para efetuar a conversão em texto.
################################################################################

# Integrando com a API do Whisper para converter o áudio em texto

#Define o tipo de modelo do Whisper a ser utilizado
model = whisper.load_model("small")

# Transcreve o audio gravado anteriormente.
#OBS.: O whisper detecta automaticamente o idioma falado no áudio, 
# então não é necessário informar o idioma para a conversão

resultado = model.transcribe(nome_arquivo_audio, fp16=False)

print ("\n [GeraLetra] Efetuando conversão... Isso pode levar alguns minutos.\n")

transcricao = resultado["text"]

# Verificando se a transcrição é vazia ou contém apenas espaços em branco. 
# Se sim, o resultado é considerado inválido e a rotina é encerrada

verifica_transcricao = transcricao.strip()

if verifica_transcricao == "":
  print ( "O conversor identificou que vídeo informado é instrumental, sem som ou com uma instrodução maior do que 30 segundos e não pode ser transcrito. Por favor, informe outro vídeo que não tenha essas caracteristicas")
  exit()

#Após a conversão, o resultado é exibido na tela e o sistema pergunta ao usuário 
# se ele deseja colocar o conteúdo na área de trabalho. 
# Se sim, o texto vai para a área de trabalho e a rotina se encerra

resposta_usuario = input ("A letra do áudio foi extraída com sucesso! Deseja copiar o resultado para a área de transferência? (S/N) \n").upper()

while resposta_usuario not in ['S', 'N']:
  print ("Resposta inválida! Por favor, responda com S para SIM ou N para NÃO. \n")
  resposta_usuario = input ("Deseja copiar o resultado para a área de transferência? (S/N) \n").upper() 

if resposta_usuario == 'S': 
    # Vamos formatar o texto de acordo com o que ele é: Texto corrido ou letra de música
    # Quem vai fazer isso é a IA. Vamos usar o Gemini para 
    
    # Configurando a credencial
    client = genai.Client(api_key=api_key_gemini)

     # Prompt Mestre
    prompt_sistema = "Atue como um Editor de Textos Profissional e Especialista em Linguística. " \
    "Recebi uma transcrição bruta de áudio (gerada por IA) que não possui quebras de linha, " \
    "parágrafos ou formatação de versos. Sua tarefa é processar o texto abaixo seguindo estas regras: " \
    "Identificação de Gênero: Analise se o texto é uma música/poema ou um discurso/diálogo/narração. " \
    "Se for Música/Poema: Formate o texto em versos e estrofes. " \
    "Identifique o refrão e separe-o com linhas em branco. " \
    "Mantenha a rima e a métrica visíveis. " \
    "Se for Discurso/Narração: Organize em parágrafos de acordo com a norma culta, " \
    "quebrando o texto sempre que houver uma mudança de tópico, ideia ou interlocutor. " \
    "Fidelidade: Não altere, não adicione e não remova nenhuma palavra. " \
    "Apenas pontue e formate o layout." \
    "Caso reconheça o texto como uma letra de música, adicione a tag [LETRA DE MÚSICA] no início do resultado. " \
    "Caso reconheça o texto como um discurso, diálogo ou narração, adicione a tag [TEXTO CORRIDO] no início do resultado. " \
    "Importante: Não coloque seus comentários ou explicações no resultado. APENAS o Texto Formatado" \
    " \n TEXTO BRUTO:"

    # Incuilindo o texto que veio do Whisper
    texto_bruto = transcricao.strip() 

    # A chamada para a API do Gemini, passando o prompt e o texto bruto para formatação
    response = client.models.generate_content(
      model="gemini-2.5-flash",       
      contents=f"{prompt_sistema}\n\n{texto_bruto}")

    #Colocando o resultado na área de transferència   
    pyperclip.copy(response.text) 
    print ("O resultado foi copiado para a área de transferência com sucesso! Agora é só colar em um editor de texto! \n")
    print ("Obrigada por usar o GeraLetra! Até a próxima! \n")

else: #Para a exibição em tela não há a formatação pelo agente de IA
   print ("O resultado será exibido em tela:\n")
   print ("------------------------------\n")
   print (transcricao.strip() + "\n" )
   print ("------------------------------\n")
   print ("Obrigada por usar o GeraLetra! Até a próxima! \n")

#Tudo certo, vamos limpar os arquivos temporários criados para não ocupar espaço desnecessário
os.remove(nome_arquivo_audio)
exit()