import re
import os
import sys

class Parser:
    MATCH_CONTEUDO_COMANDO    = re.compile(r"(?<={)(.*)(?=})")
    MATCH_NOME_COMANDO        = re.compile(r"(?<=\\)([A-z]*)")
    MATCH_TITULO              = re.compile(r"(\\title\s*{)(.*)(})")
    MATCH_AUTOR               = re.compile(r"(\\author\s*{)(.*)(})")
    MATCH_SECAO               = re.compile(r"\\(sub)*section(\*|){(.*)}")
    MATCH_DOCUMENTO           = re.compile(r"(?<=\\begin{document})(.*\n+)*(?=\\end{document})")
    MATCH_COMANDO             = re.compile(r"(\s|)\\([A-z]*)(\*|)({.*}|\s)")
    MATCH_COMENTARIO_LINHA    = re.compile(r"(^|(?<=[^\\]))%(.*)")
    MATCH_COMENTARIO_AMBIENTE = re.compile(r"(\\begin{comment})(.*\n+)*(\\end{comment})")

    def __init__(self, arquivo):
        self.arquivo      = arquivo
        self.titulo       = ''
        self.autor        = ''
        self.texto        = ''
        self.codigo_fonte = ''
        self.secoes       = []
        self.paragrafos   = []
        self.palavras     = []
        self.frases       = []
        try:
            arq = open(arquivo,encoding='iso8859-1')
            for linha in arq:
                self.codigo_fonte += linha
            self.__parse()
            arq.close()
        except OSError:
            print("Erro ao ler arquivo + '" + arquivo + "'")

    def __get_conteudo_comando(self, cmd):
        s = self.MATCH_CONTEUDO_COMANDO.search(cmd)
        if s:
            return s.group()
        return ''

    def __get_nome_comando(self, cmd):
        s = self.MATCH_NOME_COMANDO.search(cmd)
        if s:
            return s.group()
        return ''

    def __get_titulo(self, cod):
        s = self.MATCH_TITULO.search(cod)
        if s:
            return self.__get_conteudo_comando(s.group())
        return ''

    def __get_autor(self, cod):
        s = self.MATCH_AUTOR.search(cod)
        if s:
            return self.__get_conteudo_comando(s.group())
        return ''

    def __get_secoes(self, cod):
        ret = []
        it = self.MATCH_SECAO.finditer(cod)
        for n in it:
            ret.append(self.__get_conteudo_comando(n.group()))
        return ret

    def __get_documento(self, cod):
        s = self.MATCH_DOCUMENTO.search(cod)
        if s:
            return s.group()
        return ''

    def __apagar_comandos(self, cod):
        s = self.MATCH_COMANDO.search(cod)
        while s:
            cmd = s.group()
            cod = cod.replace(cmd,'')
            s = self.MATCH_COMANDO.search(cod)
        return cod
	
    def __get_texto(self, cod):
        doc = self.__get_documento(cod)
        return self.__apagar_comandos(doc)

    def __get_paragrafos(self, texto):
        p = texto.split('\n\n')
        f = lambda t: t != ''
        g = lambda t: t.replace('\n',' ').strip()
        return list(filter(f,map(g,p)))

    def __get_frases(self, texto):
        frases = texto.split('.')
        f = lambda t: t != ''
        return list(filter(f,frases))
	
    def __get_palavras(self, texto):
        return texto.split()

    def __remover_comentarios(self, cod):
        cod = re.sub(r"(?<=[^\\])%(.*)",'',cod)
        return re.sub(r"(\\begin\s*{comment})(.*\n+)*(\\end\s*{comment})",'',cod)

    def __parse(self):
        cod             = self.__remover_comentarios(self.codigo_fonte)
        self.titulo     = self.__get_titulo(cod)
        self.autor      = self.__get_autor(cod)
        self.texto      = self.__get_texto(cod)
        self.secoes     = self.__get_secoes(cod)
        self.paragrafos = self.__get_paragrafos(self.texto)
        self.frases     = self.__get_frases(self.texto)
        self.palavras   = self.__get_palavras(self.texto)

    def get_arquivo(self):
        return self.arquivo

    def get_titulo(self):
        return self.titulo

    def get_autor(self):
        return self.autor

    def get_texto(self):
        return self.texto

    def get_secoes(self):
        return self.secoes

    def get_paragrafos(self):
        return self.paragrafos

    def get_frases(self):
        return self.frases

    def get_palavras(self):
        return self.palavras

class SeparadorSilabico:
    VOGAL           = ('a','e','i','o','u','á','é','ó','í','ú','ã','õ','â','ê','ô','à')
    SEMI_VOGAL      = ('i','u')
    VOGAL_ACENTUADA = ('á','é','ó','í','ú','ã','õ','â','ê','ô','à')

    def __init__(self):
        pass
	
    def __ditongo(self, s):
        if len(s) < 2:
            return False
        return s[1] in self.VOGAL and s[1] not in self.VOGAL_ACENTUADA
	
    def __tritongo(self, s):
        if len(s) < 3:
            return False
        return (s[0] in self.SEMI_VOGAL and s[1] in self.VOGAL and s[2] in self.SEMI_VOGAL) or s == 'uão'

    def contar_silabas(self, palavra):
        palavra = palavra.lower()
        c = i = 0
        while i < len(palavra):
            if palavra[i] in self.VOGAL:
                c += 1
                if self.__tritongo(palavra[i:i+3]):
                    i += 3
                    continue
                elif self.__ditongo(palavra[i:i+2]):
                    i += 2
                    continue
            i += 1
        return c

class Corretor:
    TERMOS_GEN = ('milhares','diversas','diversos','nenhum','nenhuma','tudo','pouco','pouca','muito','muita','várias','vários')
    def __init__(self, documento):
        self.documento = documento
	
    def __erro_secao_unica(self):
        if len(self.documento.get_secoes()) == 1:
            return 'Seção única; '
        return ''

    def __erro_sem_titulo(self):
        if self.documento.get_titulo() == '':
            return 'Documento sem título; '
        return ''

    def __erro_paragrafo_uma_frase(self):
        pass

    def __erro_termo_generalizante(self):
        txt = self.documento.get_texto().lower()
        for t in self.TERMOS_GEN:
            if re.search(r"\b" + re.escape(t) + r"\b",txt):
                return "Uso de termo generalizante '" + t + "'; "
        return ''

    def __erro_grafia_brasil(self):
        txt = self.documento.get_texto()
        if re.search(r"\bbrasil\b",txt):
            return "Grafia incorreta do nome 'Brasil'; "
        return ''

    def __erro_termo_coloquial(self):
        txt = self.documento.get_texto().lower()
        if re.search(r"\bpra\b",txt) or re.search(r"\bpro\b",txt):
            return "Uso de termo coloquial 'pra' ou 'pro'; "
        return ''

    def __erro_etc(self):
        txt = self.documento.get_texto().lower()
        if txt.find('e etc') > -1:
            return "Uso de 'e etc' no lugar de apenas 'etc'; "
        return ''

    def __erro_pontuacao_titulos(self):
        secoes = self.documento.get_secoes()
        for s in secoes:
            if s != '':
                if s[-1] == '.' or s[-1] == ':':
                    return "Uso de ponto final ou dois pontos na secao '" + s + "'; "
        return ''

    def __erro_espaco_pontuacao(self):
        txt = self.documento.get_texto()
        if txt.find(' .') > -1:
            return 'Espaço antes de ponto final; '
        if txt.find(' ,') > -1:
            return 'Espaço antes de vírgula; '
        if txt.find(' :') > -1:
            return 'Espaço antes de dois pontos; '
        if txt.find(' ?') > -1:
            return 'Espaço antes de interrogação; '
        if txt.find(' !') > -1:
            return 'Espaço antes de exclamação; '
        if txt.find(' ;') > -1:
            return 'Espaço antes de ponto e vírgula; '
        if txt.find('( ') > -1:
            return 'Espaço após abertura de parênteses; '
        if txt.find(' )') > -1:
            return 'Espaço antes do fechamento de parênteses; '
        return ''

    def __erro_aspas(self):
        if self.documento.get_texto().find('"') > -1:
            return "Uso incorreto das aspas. Corrija para `` ''; "
        return ''

    def __erro_reticencias(self):
        if self.documento.get_texto().find('etc...') > -1:
            return "Uso de reticências após 'etc'; "
        return ''

    def listar_erros(self):
        erros = ''
        erros += self.__erro_secao_unica()
        erros += self.__erro_sem_titulo()
        erros += self.__erro_termo_generalizante()
        erros += self.__erro_grafia_brasil()
        erros += self.__erro_termo_coloquial()
        erros += self.__erro_etc()
        erros += self.__erro_pontuacao_titulos()
        erros += self.__erro_espaco_pontuacao()
        erros += self.__erro_aspas()
        erros += self.__erro_reticencias()
        return erros

class FleschBR:
    def __init__(self, documento):
        self.documento = documento

    def __get_palavras(self, texto):
        return texto.split()

    def __get_frases(self, texto):
        frases = texto.split('.')
        f = lambda t: t != ''
        return list(filter(f,frases))

    def __contar_silabas(self, palavras):
        s = SeparadorSilabico()
        c = 0
        for p in palavras:
            c += s.contar_silabas(p)
        return c

    def indice(self, texto):
        p = self.__get_palavras(texto)
        f = self.__get_frases(texto)
        total_palavras = len(p)
        total_frases   = len(f)
        total_silabas  = self.__contar_silabas(p)
        return 248.835 - (1.015 * (total_palavras/total_frases)) - (84.6 * (total_silabas/total_palavras))

    def indice_paragrafos(self):
        r = []
        paragrafos = self.documento.get_paragrafos()
        for p in paragrafos:
            r.append(self.indice(p))
        return r

    def grau(self, indice):
        if indice < 25:
            return 'Muito Difícil (Ensino Superior)'
        elif indice >= 25 and indice < 50:
            return 'Difícil (Ensino Médio)'
        elif indice >= 50 and indice < 75:
            return 'Fácil (6º a 9º ano)'
        else:
            return 'Muito Fácil (1º a 5º ano)'

def analisar_arquivo(arq):
    p = Parser(arq)
    f = FleschBR(p)
    c = Corretor(p)
    print('Arquivo: ' + p.get_arquivo())
    print('Autor  : ' + p.get_autor())
    print('Título : ' + p.get_titulo())
    cont = 1
    for i in f.indice_paragrafos():
        print('Leiturabilidade paragrafo {}: {:.2f} - {}'.format(cont,i,f.grau(i)))
        cont += 1
    leit = f.indice(p.get_texto())
    print('Leiturabilidade geral: {:.2f} - {}'.format(leit,f.grau(leit)))
    print('Erros encontrados: ' + c.listar_erros())
    print()

def analisar_diretorio_recursivo(root):
    for e in os.listdir(root):
        x = os.path.join(root,e)
        if os.path.isdir(x):
            analisar_diretorio_recursivo(x)
        elif e.endswith('.tex'):
            analisar_arquivo(x)
def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isdir(arg):
            analisar_diretorio_recursivo(arg)
        else: 
            if arg.endswith('.tex'):
                analisar_arquivo(arg)
            else:
                print('Forneça um arquivo LaTeX (.tex)')
    else:
        print('Forneça um arquivo LaTeX ou um diretório')

if __name__ == '__main__':
    main()
