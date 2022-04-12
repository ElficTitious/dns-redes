from operator import sub
from pickle import TRUE
import socket
from dnslib import DNSRecord
import dnslib
from dnslib.dns import CLASS, QTYPE

def send_dns_message(query_name: str, address: str) -> DNSRecord:
  """Función usada para enviar mensaje DNS preguntando por el dominio query_name
  a la dirección address, donde se retorna el DNSRecord resultante.

  Parameters:
  -----------

  query_name (str): Dominio por el cual se está consultando.
  address (str): Dirección a la cual se consulta por el dominio.

  Returns:
  --------

  (DNSRecord): Mensaje DNS resultante de la consulta.
  """
  # Acá ya no tenemos que crear el encabezado porque dnslib lo hace por nosotros, por default pregunta por el tipo A
  qname = query_name
  q = DNSRecord.question(qname)
  server_address = (address, 53)
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    # lo enviamos, hacemos cast a bytes de lo que resulte de la función pack() sobre el mensaje
    sock.sendto(bytes(q.pack()), server_address)
    # En data quedará la respuesta a nuestra consulta
    data, _ = sock.recvfrom(4096)
    # le pedimos a dnslib que haga el trabajo de parsing por nosotros
    d = DNSRecord.parse(data)
  finally:
    sock.close()
  # Ojo que los datos de la respuesta van en en una estructura de datos
  return d

def parse_domain(url: str) -> list[str]:
  """Función que parsea un dominio retornando una lista con todos los
  subdominios necesarios para resolver la ip correspondiente al dominio.
  
  Ejemplo:
  --------

  parse_domain("eol.uchile.cl.") = [".", "cl.", "uchile.cl.", "eol.uchile.cl."]

  Parameters:
  -----------

  url (str): Dominio a partir del cual generar la lista de subdominios.

  Returns:
  --------

  (list[str]): Lista de subdominios necesarios para resolver la ip del dominio url.
  """
  substring = ['.']
  sub_addresses = ['.'] # Inicilizamos la lista con la raiz "."
  for i in range(len(url) - 2, -1, -1):
    curr_char = url[i]
    if url[i] == '.':
      # Al llegar a u '.' añadimos el substring generado
      substring = ''.join(substring)
      sub_addresses.append(substring)
      substring = substring.split()

    substring.insert(0, curr_char)

  # Agregamos la última sub-dirección
  substring = ''.join(substring)
  sub_addresses.append(substring)
  
  return sub_addresses


class Cache:
  """Clase usada para representar un cache, el cual es utilizado por un
  DNSResolver para guardar el ip correspondiente a los 10 dominios mas
  consultados entre las últimas 100 consultas.

  Attributes:
  -----------

  cache (list[tuple[str, str]]): Lista de pares (dominio, ip) --ip puede ser
                                 también un name server--.
  """

  def __init__(self):
    self.cache = []
    # Campo privado donde guardar los 100 últimos pares (dominio, ip) consultados.
    self.__stack = []

  def __push_in_stack(self, domain_ip_pair: tuple[str, str]) -> None:
    """Método privado usado para guardar una consulta en el stack.

    Parameters:
    -----------

    domain_ip_pair (tuple[str, str]): Par (dominio, ip) a guardar en el stack.
    """
    self.__stack.append(domain_ip_pair)
    # Si luego de pushear el par en el stack el largo supera 100, quitamos el ultimo
    # elemento.
    if len(self.__stack) > 100:
      self.__stack.pop(0)

  def __generate_cache(self) -> None:
    """Método usado para generar el cache a partir del stack de últimas 100
    consultas.
    """
    l = []
    # En primer lugar generamos una lista auxiliar sin duplicados a partir
    # del stack.
    stack_no_dups = list(dict.fromkeys(self.__stack))
    # Para cada elemento en la lista auxiliar guardamos en l un par correspondiente
    # al elemento y sus ocurrencias en el stack.
    for domain_ip_pair in stack_no_dups:
      l.append((domain_ip_pair, self.__stack.count(domain_ip_pair)))
    # Ordenamos la lista en base a las ocurrencias (en orden reverso).
    l.sort(key=lambda x: x[1], reverse=True)
    # Nos quedamos con solo los pares (dominio, ip) y asignamos los primeros 10
    # elementos al cache.
    l = [x[0] for x in l]
    self.cache = l[:10]

  def update_cache(self, domain_ip_pair: tuple[str, str]) -> None:
    """Método usado para actualizar el caché con un nuevo par (dominio, ip).
    Solo se usará en casó de registar un par actualmento no almacenado en el
    caché.

    Parameters:
    -----------

    domain_ip_pair (tuple[str, str]): Par (dominio, ip) a guardar en el caché.
    """
    # En primer lugar pusheamos el par en el stack.
    self.__push_in_stack(domain_ip_pair)
    # Luego genearmos el caché
    self.__generate_cache()

  def search_cache(self, domain: str) -> tuple[bool, str]:
    """Método usado para buscar un dominio en el caché, donde en caso de estár en
    el caché se actualiza el stack y caché para reflejar la nueva consulta.

    Parameters:
    -----------

    domain (str): Dominio a buscar en el caché.

    Returns:
    --------

    (tuple[bool, str]): Par representando si el dominio se encuentra en cache junto
                        con la ip. En caso de no estar en el caché como segundo elemento
                        se retorna el string vacio.
    """
    for i in range(len(self.cache)):
      if domain == self.cache[i][0]:
        # Si el elemento está en el cache se actualiza el stack y se genera nuevamente
        # el caché.
        self.update_cache((domain, self.cache[i][1]))
        return True, self.cache[i][1]
    
    return False, ''


class DNSReply:
  """Clase auxiliar usada para representar una respuesta DNS.

  Attributes:
  -----------

  data (str): Respuesta asociada a una consulta DNS (puede ser IP, SOA o NS).
  responds_with_ip (bool): Booleano usado para representar si la respuesta es
                           o no una IP. 
  """

  data: str

  def __init__(self, dnslib_reply: DNSRecord):

    # header section
    number_of_answer_elements = dnslib_reply.header.a
    number_of_authority_elements = dnslib_reply.header.auth

    self.responds_with_ip = False

    # answer section
    if number_of_answer_elements > 0:
      first_answer = dnslib_reply.get_a() # primer objeto en la lista all_resource_records
      answer_rdata = first_answer.rdata # rdata asociada a la respuesta
      self.responds_with_ip = True
      self.data = str(answer_rdata)

    # authority section
    if number_of_authority_elements > 0:
      authority_section_list = dnslib_reply.auth # contiene un total de number_of_authority_elements
      authority_section_RR_0 = authority_section_list[0] # objeto tipo dnslib.dns.RR
      authority_section_0_rdata = authority_section_RR_0.rdata
      # si recibimos auth_type = 'SOA' este es un objeto tipo dnslib.dns.SOA
      if isinstance(authority_section_0_rdata, dnslib.dns.SOA):
        primary_name_server = authority_section_0_rdata.get_mname()  # servidor de nombre primario
        self.data = str(primary_name_server)
    
      elif isinstance(authority_section_0_rdata, dnslib.dns.NS) and not self.responds_with_ip: # si en vez de SOA recibimos un registro tipo NS
        name_server_domain = authority_section_0_rdata # entonces authority_section_0_rdata contiene el nombre de dominio del primer servidor de nombre de la lista
        self.data = str(name_server_domain)