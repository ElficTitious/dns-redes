from utilities import *
import socket
from dnslib import DNSRecord, DNSHeader, DNSQuestion, RR, A

class DNSResolver:
  """Clase estática usada para representar un DNS Resolver
  """

  def __recv_domain_name_dns_msg(socket: socket) -> tuple[str, str, str]:
    """Método usado para recibir el dominio a resolver desde el cliente.

    Parameters:
    -----------

    socket (socket): Socket desde el cual recibir el mensaje DNS con el dominio
                     por el cual se consulta.

    Returns:
    --------

    (tuple[str, str, str]): 3-tupla con el nombre del dominio por el cual se consulta, dirección
                            del cliente para posteriormente responder, y id del mensaje también
                            para la respuesta.
    """
    data, client_addr = socket.recvfrom(4096)  # Recibimos el mensaje
    d = DNSRecord.parse(data)  # Parseamos
    dom_id = d.header.id  # Guardamos la id de la consulta
    first_query = d.get_q()  # primer objeto en la lista all_querys
    domain_name_in_query = first_query.get_qname() # nombre de dominio por el cual preguntamos

    return str(domain_name_in_query), client_addr, dom_id
  
  def __search_ip_of_domain(cache: Cache, domain: str, addr: str) -> str:
    """Método usado para consultar por un dominio en una dirección teniendo
    el cuenta la posible existencia de la respuesta en un cache.

    Parameters:
    -----------

    cache (Cache): Cache siendo utilizado al momento de realizar la consulta.
    domain (str): Dominio por el cual se consulta.
    addr (str): Dirección a la cual se consulta por el dominio.

    Returns:
    --------

    (str): Resultado de la consulta (puede ser una IP, SOA o NS).
    """
    root_addr = '8.8.8.8'

    # Si existe registro del dominio en el caché retornamos el valor almacenado
    # sin realizar consultas DNS adicionales.
    is_in_cache, ip = cache.search_cache(domain)
    if is_in_cache:
      print('Responde el cache! ')
      return ip

    # De lo contrario realizamos la consulta DNS pertinente.
    d1 = send_dns_message(domain, addr)
    d2 = DNSReply(d1)

    # Si se responde con una IP actualizamos el caché y retornamos inmediatamente
    if d2.responds_with_ip:
      cache.update_cache((domain, d2.data))
      return d2.data
    
    # De lo contrario se respondió con un SOA o NS, para el cual repetimos el proceso.
    ns_addr: str
    ns_is_in_cache, ns_ip = cache.search_cache(d2.data)
    if ns_is_in_cache:
      ns_addr = ns_ip
    
    else:
      d3 = send_dns_message(d2.data, root_addr)
      d4 = DNSReply(d3)
      ns_addr = d4.data
      cache.update_cache((d2.data, ns_addr))
    
    return ns_addr


  @classmethod
  def run(cls) -> None:
    """Método usado para correr el DNS Resolver.
    """

    cache = Cache()  # Instanciamos el caché

    # Instanciamos el socket a usar y asociamos a (localhost, 5353)
    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dgram_socket.bind(('127.0.0.1', 5353))

    while True:
      
      # Rescatamos el nombre de dominio consultado, dirección e id del cliente
      domain_name, client_addr, dom_id = cls.__recv_domain_name_dns_msg(dgram_socket)
      links_in_request = parse_domain(domain_name)  # Parseamos el dominio en subdominios.

      addr = '8.8.8.8'
      # Para cada dominio en la lista de subdominios links_in_request realizamos una consulta.
      for domain in links_in_request:
        addr = cls.__search_ip_of_domain(cache, domain, addr)

      # Finalmente generamos el DNSRecord correspondiente a la respuesta, donde debemos agregar
      # el id de la consulta original para que la respuesta sea resuelta por el cliente.
      resp = DNSRecord(DNSHeader(id=dom_id, qr=1,aa=1,ra=1),
                       q=DNSQuestion(domain_name),
                       a=RR(domain_name,rdata=A(addr)))

      # Enviamos la respuesta a la dirección original del cliente.
      dgram_socket.sendto(bytes(resp.pack()), client_addr)

      print(domain_name, 'corresponde a la IP: ', addr)

# MAIN: solo corremos el resolver.
if __name__ == "__main__":
  
  DNSResolver.run()
