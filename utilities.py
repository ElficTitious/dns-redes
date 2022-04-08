from operator import sub
from pickle import TRUE
import socket
from dnslib import DNSRecord
import dnslib
from dnslib.dns import CLASS, QTYPE

def send_dns_message(query_name: str, address: str) -> DNSRecord:
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
  substring = ['.']
  sub_addresses = ['.']
  for i in range(len(url) - 2, -1, -1):
    curr_char = url[i]
    if url[i] == '.':
      substring = ''.join(substring)
      sub_addresses.append(substring)
      substring = substring.split()

    substring.insert(0, curr_char)

  # Agregamos la última sub-dirección
  substring = ''.join(substring)
  sub_addresses.append(substring)
  
  return sub_addresses


class DNSReply:

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
