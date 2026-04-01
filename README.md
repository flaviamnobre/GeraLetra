# GeraLetra - MVP
Desafio do Bootcamp DIO com IA e Reconhecimento de Voz - Dada um video curto no YouTube, retorna a letra do audio, de acordo com o tipo de conteúdo do vídeo: Música, discurso, diálogo, etc... 

**Descrição**  
A partir de uma URL do Youtube retorna a letra que está no audio do vídeo, no formato específico para letras de música, ou texto corrido, caso seja um discurso, diálogo ou narração. O resultado pode ser copiado para a área de transferência.

Se for uma música, o texto é formatado em versos e estrofes, com o refrão separado por linhas em branco. 

Se for um discurso, diálogo ou narração, o texto é organizado em parágrafos de acordo com a norma culta, quebrando o texto sempre que houver uma mudança de tópico, ideia ou interlocutor. O sistema não altera, não adiciona e não remove nenhuma palavra do texto original, apenas pontua e formata o layout.


**Pipeline de IAs:**  
Há a interação entre dois agentes de IA: Whisper para converter o áudio extraído em texto e Gemini para formatar o texto de acordo com o que ele é: Texto corrido ou letra de música. 

 ==> O modelo do Gemini escolhido é o Gemini-2.5-flash, que é gratuito. O GPT-4 é pago, então não foi possível utilizar nessa versão MVP.

 **MVP:**   
Geração simples, dada a URL, retorna a letra formatada, com opção de colocar o resultado na área de transferência, formatado de acordo com o tipo de conteúdo do vídeo informado

**GeraLetra - MVP (v1.0)**  

📝 **Descrição do Projeto**  


O GeraLetra é uma ferramenta de automação que extrai áudio de vídeos do YouTube e utiliza Inteligência Artificial para transcrever e formatar o conteúdo. O diferencial está na capacidade de distinguir entre música (formatando em versos e estrofes) e discurso/narração (organizando em parágrafos seguindo a norma culta), entregando um texto pronto para uso profissional.

🛠️ **Requisitos de Ambiente (Setup)**  
Para rodar este script, é preciso preparar o ambiente com os seguintes componentes:

**1. Dependências do Sistema (Software)**  
* Python 3.8+: Linguagem base do projeto
* FFmpeg: Essencial
   É o motor que extrai o áudio do vídeo. Deve estar instalado no sistema e adicionado ao PATH (variáveis de ambiente).

**2. Bibliotecas Python (Instalação via PIP)** 
* **openai-whisper**
  É a Inteligência Artificial de Speech-to-Text (Transformação de fala em texto).
  ==> Recebe o arquivo MP3 baixado e "ouve" o áudio para gerar a transcrição bruta (o texto sem pontuação ou parágrafos).

* **yt-dlp**
  Ferramenta de linha de comando para baixar vídeos e áudios de plataformas como o YouTube.
  ==> É o responsável por acessar a URL que o usuário informa e extrair apenas o áudio do vídeo com a melhor qualidade disponível.

* **google-api-python-client**
  Cliente oficial para acessar as diversas APIs do Google Cloud.
  ==> Conecta o script à YouTube Data API v3 para que você possa consultar metadados do vídeo (como verificar se ele é real ou qual a duração exata dele em segundos).

* **google-genai**
 SDK oficial para interagir com os modelos Gemini da Google.  
  ==> Envia o texto bruto do Whisper para o Gemini-2.5-Flash junto com o seu "Prompt Mestre", recebendo de volta o texto perfeitamente formatado.

* **python-dotenv**  
  Lê variáveis de configuração de um arquivo externo chamado .env.
  ==> Papel no projeto: Garante a segurança do código, impedindo que suas chaves de API fiquem escritas diretamente no script (Hardcoded).

* **pyperclip**
  Biblioteca simples que interage com a área de transferência (Clipboard) do sistema operacional.
  ==> Permite que o resultado final da letra/texto seja enviado para o "Ctrl+C" do usuário automaticamente.

* **isodate**
  Utilitário para lidar com datas e durações no padrão ISO 8601.
  ==> A API do YouTube retorna a duração do vídeo em um formato estranho (ex: PT5M30S). O isodate converte isso para segundos reais para que seu código possa validar se o vídeo tem menos de 10 minutos.

==> Execute o comando abaixo para instalar todas as dependências:  
pip install openai-whisper yt-dlp google-api-python-client python-dotenv google-genai pyperclip isodate

**4. API KEYs Necessárias**
As chaves necessárias são as seguintes:  
* *YouTube Data API v3*: Para consultar metadados e duração dos vídeos.
* *Gemini API (Google AI Studio)*: Para a inteligência de formatação de texto (modelo Gemini-2.5-Flash).

⚙️ *Configuração (Arquivo .env)*
É necessário um arquivo chamado *.env* na raiz do projeto. Ele traz as configurações e informações necessárias ao funcionamento que não se encontram dentro do código. 
Para o MVP é preciso apenas que sejam informadas as API KEYS necessárias ao funcionamento. O conteúdo do arquivo deve ser apenas as duas linhas abaixo

GEMINI_API_KEY=sua_chave_aqui
YOUTUBE_API_KEY=sua_chave_aqui

==> Substitua a variável *sua_chave_aqui* pelas respectivas API Keys
==> O arquivo deve chamar-se apenas ".env", sem nenhum caracter antes do ponto. Isso porque é o padrão do Python, ele busca exatamente por este arquivo.

📋 **Regras de Negócio**

* **RN01. Limite de Tempo:** O sistema somente aceita vídeos com duração máxima de 10 minutos.
* **RN02. Validação de Fonte:** Apenas URLs válidas do domínio YouTube (curtas ou longas) são processadas.
* **RN03. Fidelidade Textual:** A IA de formatação não pode alterar, adicionar ou remover nenhuma palavra do texto original, apenas ajustar pontuação e layout.

🚀 **Requisitos Funcionais**

* **RF01. Validação de URL:** Identifica links inválidos ou que não pertencem ao YouTube.

* **RF02. Checagem de Metadados:** Verifica se o vídeo existe, se é uma transmissão ao vivo ou se tem duração zero.

* **RF03. Extração de Áudio:** Converte o vídeo em formato MP3 de alta qualidade.

* **RF04. Transcrição Automática:** Utiliza o modelo Whisper (small) para transformar áudio em texto bruto.

* **RF05. Identificação de Gênero:** Detecta se o áudio é musical ou falado.

* **RF06.Formatação Inteligente:** Aplica quebras de linha, estrofes e tags identificadoras ([LETRA DE MÚSICA] ou [TEXTO CORRIDO]).

* **RF07.Integração com Clipboard:** Permite copiar o resultado final diretamente para a área de transferência do Windows/Mac/Linux.

🏗️ **Arquitetura do Pipeline de IA**
O projeto utiliza um encadeamento de modelos (Chaining):

* Whisper (OpenAI): Responsável pelo reconhecimento de fala (STT - Speech-to-Text).

* Gemini (Google): Atua como um Agente de Refinamento Linguístico e Editor de Texto.

Arquivos de áudio são salvos em uma pasta temporária (temp_geraletra) e deletados automaticamente ao fim da execução.


**ETAPAS FUNCIONAIS**
  1. Receber a URL do Usuário  
  Solicitar a entrada de uma URL ao usuário e efetuar as devidas validações

  2.Verificar a duração do arquivo fornecido  
  Dada a URL válida, observar os metatados e verificar a duração do arquivo
   
  3 - Extrain o arquivo mp3 do Video do YouTube  
  A partir da URL válida, de um vídeo de até 10 minutos de duração, salvar TEMPORARIAMENTE o audio em um formato válido para a extração do texto

  4 - Executar a conversão em texto a partir do audio  
  Com o arquivo de audio, usar o Whisper para efetuar a conversão em texto.

  5 - Exibir na tela o resultado com a opção de colocar na área de trabalho  
  Após a conversão, o resultado é exibido na tela e o sistema pergunta ao usuário se ele deseja colocar o conteúdo na área de trabalho. Se sim, o texto vai para a área de trabalho e a rotina se encerra

