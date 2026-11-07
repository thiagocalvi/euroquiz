-- Questões
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL CHECK (level IN ('facil', 'medio', 'dificil', 'final')),
    statement TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option CHAR(1) NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D'))
);

-- Histórico de Jogo
-- Registra toda ação realizada pelo jogador e mantém o estado completo do jogo
-- para que qualquer um dos 3 servidores (via Round-Robin) possa continuar a partida.
CREATE TABLE IF NOT EXISTS game_history (
    id SERIAL PRIMARY KEY,
    nickname VARCHAR(50) NOT NULL,
    action_type VARCHAR(30) NOT NULL,
    question_order INT NOT NULL CHECK (question_order BETWEEN 1 AND 10),
    question_level VARCHAR(10) NOT NULL CHECK (question_level IN ('facil', 'medio', 'dificil', 'final')),
    current_question_id INT NOT NULL REFERENCES questions(id),
    asked_question_ids TEXT NOT NULL,
    eliminated_options VARCHAR(10) DEFAULT '',
    used_half BOOLEAN NOT NULL DEFAULT FALSE,
    used_skip BOOLEAN NOT NULL DEFAULT FALSE,
    used_free_pass BOOLEAN NOT NULL DEFAULT FALSE,
    score NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL CHECK (status IN ('IN_PROGRESS', 'LOST', 'WON')),
    question_started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    server_name VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_game_history_nickname_id ON game_history (nickname, id DESC);
CREATE INDEX IF NOT EXISTS idx_game_history_status_score ON game_history (status, score DESC);

-- NÍVEL FÁCIL
INSERT INTO questions (level, statement, option_a, option_b, option_c, option_d, correct_option) VALUES
('facil', 'De maneira geral, como o país sede do Eurovision é definido?', 'Por meio de sorteio', 'Por voluntariado', 'O atual campeão se torna o país sede', 'Por voto popular', 'C'),
('facil', 'Qual a maior nota que um país pode receber dentro do Eurovision, o famoso "Douze points"?', '5 Pontos', '12 Pontos', '20 Pontos', '24 Pontos', 'B'),
('facil', 'O Eurovision é uma competição de:', 'Música', 'Talentos', 'Jogos', 'Esportes', 'A'),
('facil', 'Dentro do Eurovision, o termo "Nul Points" indica o que?', 'Que o pais recebeu a maior pontuação somada possível', 'Que o país é campeão dois anos consecutivos', 'Que o país recebeu um total de 67 pontos', 'Que o país recebeu nenhum ponto', 'D'),
('facil', 'Qual é o slogan oficial do Eurovision, adotado em 2023?', '"Open up"', '"United by Music"', '"Beating Heart"', '"The Beauty of Sound"', 'B'),
('facil', 'O Eurovision é um evento que surgiu em qual continente?', 'América', 'Ásia', 'Europa', 'África', 'C'),
('facil', 'A Irlanda e Suécia são os países com a maior quantidade de vitórias, com ambos tendo:', '2 Títulos', '4 Títulos', '5 Títulos', '7 Títulos', 'D'),
('facil', 'O Eurovision possui quantas semi-finais?', '2 Semi-finais', '3 Semi-finais', '4 Semi-finais', '5 Semi-finais', 'A'),
('facil', 'O Eurovision ocorre de quantos em quantos anos?', 'A cada 1 ano', 'A cada 2 anos', 'A cada 4 anos', 'A cada 10 anos', 'A'),
('facil', 'A música vencedora do Eurovision é decidida por meio:', 'De voto inteiramente popular', 'De uma divisão meio a meio entre voto popular e júri', 'De uma decisão conjunta das emissoras', 'De voto inteiramente do júri', 'B'),
('facil', 'Em qual mês o Eurovision geralmente ocorre?', 'Janeiro', 'Março', 'Maio', 'Julho', 'C'),
('facil', 'O artista/banda vencedora do Eurovision leva para casa:', 'Um trófeu em forma de microfone', 'Uma medalha de diamante', 'Uma coroa', 'Nada', 'A');

-- NÍVEL MÉDIO
INSERT INTO questions (level, statement, option_a, option_b, option_c, option_d, correct_option) VALUES
('medio', 'Antes do evento principal do Eurovision, ocorre um desfile dos artistas participantes. Qual o nome desse desfile?', 'Palco Roxo', 'Tapete Turquesa', 'Sala Azul', 'Torre Verde', 'B'),
('medio', 'Quais são as linguas oficiais utilizadas durante o Eurovision pelos apresentadores?', 'Inglês e Francês', 'Inglês e Italiano', 'Francês e Alemão', 'Francês e Espanhol', 'A'),
('medio', 'Após cada apresentação, os artistas vão para um local especial no evento, conhecido como:', 'Hall da Fama', 'Arquibancada do Sucesso', 'Sala Verde', 'Camarim Vip', 'C'),
('medio', 'Qual a duração máxima das músicas no Eurovision?', '01;30 Minuto', '02:00 Minutos', '02:30 Minutos', '03:00 Minutos', 'D'),
('medio', 'Em qual ano Portugal conquistou sua primeira e única vitória?', '2015', '2018', '2017', '2019', 'C'),
('medio', 'Qual país não europeu participa regularmente do festival desde a edição comemorativa de 2015?', 'Brasil', 'Nova Zelândia', 'Australia', 'Japão', 'C'),
('medio', 'Qual banda italiana venceu o Eurovision em 2021 com a música Zitti e buoni e alcançou projeção internacional?', 'Måneskin', 'Subsonica', 'Los Marcianos', 'EAMEM', 'A'),
('medio', 'Qual cantora canadense venceu o Eurovision em 1988 representando a Suíça?', 'Dolly Parton', 'Celine Dion', 'Lara Fabian', 'Shania Twain', 'B'),
('medio', 'O que aconteceu pela primeira vez na história com a edição de 2020 do Eurovision?', 'Foi cancelada devido a pandemia de Covid-19', 'Foi sediada fora da Europa', 'Duas cidades sediaram o evento ao mesmo tempo', 'O Brasil participou', 'A'),
('medio', 'Qual país ostenta o recorde de participante com o maior número de edições sem nenhuma vitória no festival?', 'Islândia', 'Malta', 'Chipre', 'San Marino', 'C'),
('medio', 'A edição do Eurovision de 2023 foi realizada na cidade de Liverpool. Por qual motivo o evento não ocorreu no país campeão do ano anterior?', 'O país sede desistiu por falta de orçamento', 'Não existiam espaços que pudessem comportar o evento', 'O Reino Unido comprou os direitos de transmissão', 'A Ucrânica venceu em 2022, mas devido à guerra não pode realizar o evento', 'D'),
('medio', 'Dentro do Eurovision, existe um grupo de 5 países conhecidos como "Big Five". Quais países fazem parte desse grupo?', 'Alemanha, Espanha, Itália, Polônia e Reino Unido', 'Alemanha, França, Itália, Reino Unido e Rússia', 'Dinamarca, Finlândia, Islândia, Noruega e Suécia', 'Alemanha, Espanha, França, Itália e Reino Unido', 'D');

-- NÍVEL DIFÍCIL
INSERT INTO questions (level, statement, option_a, option_b, option_c, option_d, correct_option) VALUES
('dificil', 'Em 1969 ocorreu um evento inédito e único na história do Eurovision. O que aconteceu?', 'Uma tempestade de neve adiou a final em uma semana', 'Quatro países empataram em primeiro lugar e todos foram declarados vencedores', 'Nenhuma das músicas recebeu a pontuação mínima necessária para vencer', 'A votação foi anulada por falhas na transmissão', 'B'),
('dificil', 'Qual foi a primeira canção a vencer o Eurovision recebendo mais de 700 pontos?', '"1944" - Jamala (Ucrânia)', '"SlowMo" - Chanel (Espanha)', '"Arcade" - Duncan Laurence (Holanda)', '"Amar Pelos Dois" - Salvador Sobral (Portugal)', 'D'),
('dificil', 'Qual dessas regras sobre o uso de instrumentos no palco é verdadeira no Eurovision atual?', 'Todos os instrumentos devem ser tocados 100% ao vivo', 'Instrumentos são permitidos no palco, mas toda a música instrumental vem de uma faixa pré-gravada', 'Baterias e pianos podem ser ao vivo, mas violões e guitarras devem ser dublados', 'Instrumentos são proibidos no palco desde 1999', 'B'),
('dificil', 'Em que ano o Eurovision introduziu pela primeira vez a separação 50/50 entre júris e televoto nas semifinais e na final moderna?', '2009', '2010', '2012', '2016', 'B'),
('dificil', 'Em 2026, mais um país fora do bloco europeu além da Australia foi aceito para participar. Qual país foi esse?', 'Argentina', 'África do Sul', 'Canadá', 'Nova Zelândia', 'C'),
('dificil', 'Em 1974, a banda ABBA venceu o Eurovision pela Suécia com a música "Waterloo". Em qual país foi realizada essa edição?', 'Suécia', 'Alemanha', 'França', 'Reino Unido', 'D'),
('dificil', 'Qual é o limite máximo de pessoas permitidas no palco durante uma apresentação no Eurovision (incluindo vocalistas e dançarinos)?', '4', '5', '6', '7', 'C'),
('dificil', 'Em 2006, o grupo de heavy metal Lordi chocou a Europa ao vencer o Eurovision trajados de monstros. Qual país eles representavam?', 'Finlândia', 'Noruega', 'Suécia', 'Islândia', 'A'),
('dificil', 'Qual é a idade mínima que um artista precisa ter para poder competir no Eurovision?', '16', '18', '21', '25', 'A'),
('dificil', 'O Eurovision é organizado por qual entidade?', 'Pelo Ministério das Comunicações da União Europeia', 'Pela emissora britânica British Broadcasting Corporation (BBC)', 'Pela União Europeia de Radiodifusão (EBU)', 'Pelo Comitê Olímpico Internacional', 'C'),
('dificil', 'Qual foi a única música na história do Eurovision a vencer a competição sem ter ficado em 1º lugar nem no júri nem no televoto individualmente?', '"Running Scared" - Ell & Nikki (Azerbaijão, 2011)', '"1944" - Jamala (Ucrânia, 2016)', '"Tattoo" - Loreen (Suécia, 2023)', '"The Code" - Nemo (Suiça, 2024)', 'B'),
('dificil', 'Em 2014, a Áustria ficou mundiamente conhecida com a música "Rise Like a Phoenix". Qual era o nome da drag queen autora do título?', 'Verka Serduchka', 'DQ', 'Rupaul', 'Conchita Wurst', 'D');

-- PERGUNTA FINAL
INSERT INTO questions (level, statement, option_a, option_b, option_c, option_d, correct_option) VALUES
('final', 'O famoso sinal sonoro e tema de abertura do Eurovision é a introdução da obra clássica "Te Deum". Quem é o compositor dessa peça?', 'Marc-Antoine Charpentier', 'Jean-Baptiste Lully', 'François Couperin', 'Georg Friedrich Händel', 'A'),
('final', 'A música "Volare", uma das canções italianas mais famosas de todos os tempos, ficou em qual posição no Eurovision de 1958?', 'Primeiro Lugar', 'Terceiro Lugar', 'Quinto Lugar', 'Último Lugar', 'B'),
('final', 'Em 1993, devido ao colapso do bloco soviético e da Iugoslávia, vários novos países queriam estrear. Por isso, organizou-se uma pré-seleção chamada Kvalifikacija za Millstreet. Qual país venceu essa eliminatória prévia?', 'Croácia', 'Bósnia e Herzegovina', 'Eslovênia', 'Estônia', 'C'),
('final', 'Em 1986, Sandra Kim venceu o Eurovision pela Bélgica com "J''aime la vie". Na época, alegou-se que ela tinha 15 anos, mas depois descobriu-se sua idade real, o que levou à regra de idade mínima. Qual era a idade exata de Sandra Kim quando venceu?', '11 anos', '12 anos', '13 anos', '14 anos', 'C'),
('final', 'A transmissão da canção de Portugal ("E depois do adeus", de Paulo de Carvalho) no Eurovision teve um papel histórico fora do mundo da música. Qual foi?', 'Foi a primeira música em português a entrar nas paradas britânicas', 'Provocou a renúncia do presidente da emissora RTP', 'Foi a primeira transmissão em cores na televisão portuguesa', 'Foi o sinal secreto para o início da Revolução dos Cravos', 'D'),
('final', 'Qual é o nome do festival de música criado em 1951 que serviu diretamente de inspiração para a criação do Eurovision Song Contest em 1956?', 'Festival di Castrocaro', 'Festival della Canzone Italiana di Sanremo', 'Cantagiro', 'Un disco per l''estate', 'B'),
('final', 'Qual foi o único país que já venceu o Eurovision e que atualmente não existe mais no mapa político mundial?', 'Iugoslávia', 'União Soviética', 'Tchecoslováquia', 'Alemanha Oriental', 'A'),
('final', 'Em 1964, o Eurovision foi sediado em Copenhague. Por qual motivo essa é considerada a "edição perdida" do festival?', 'A fita com a gravação foi destruída em um incêndio na emissora nos anos 70', 'A fita original com a gravação foi roubada durante uma invasão na emissora em 1966', 'A emissora responsável perdeu a transmissão devido a um apagão nacional', 'As fitas de vídeo foram apagadas para reutilização da fita magnética', 'A'),
('final', 'Em 2019, o concurso foi sediado em Tel Aviv. Durante a contagem de pontos, qual grupo representante da islândia gerou polêmica ao empunhar faixas com a bandeira da Palestina ao vivo?', 'Hatari', 'Daði Freyr', 'Pollapönk', 'Björk', 'A'),
('final', 'Na edição de 2012 em Baku, o país anfitrião (Azerbaijão) construiu uma arena inteiramente do zero em tempo recorde para sediar o festival. Qual é o nome dessa arena?', 'Flame Towers Arena', 'Baku Crystal Hall', 'Baku Olympic Stadium', 'National Gymnasium', 'B'),
('final', 'Qual artista deu à Moldávia um de seus momentos mais virais da história da internet em 2010 com a apresentação do SunStroke Project e Olia Tira?', 'Sergey Lazarev', 'Pasha Parfeni', 'Sergey Stepanov', 'Aliona Moon', 'C'),
('final', 'Na edição de 2021 em Roterdã, a cantora Barbara Pravi ficou em 2º lugar representando a França com a música "Voilà". Além de intérprete, por qual outra contribuição marcante no universo do Eurovision ela ficou famosa?', 'Ela foi a primeira representante feminina da história a participar 3 vezes do Eurovision', 'Foi a produtora musical responsável pelo arranjo da música vencedora da Itália em 2021', 'Foi a apresentadora oficial da transmissão do festival no canal estatal francês', 'Escreveu a música "J''imagine" de Valentina, que venceu o Junior Eurovision em 2020 pela França', 'D');
