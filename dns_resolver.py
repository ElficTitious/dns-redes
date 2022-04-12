from utilities import *
import socket
from dnslib import DNSRecord, DNSHeader, DNSQuestion, RR, A

class DNSResolver:

  def __recv_domain_name_dns_msg(socket: socket) -> tuple[str, str, str]:

    data, client_addr = socket.recvfrom(4096)
    d = DNSRecord.parse(data)
    dom_id = d.header.id
    first_query = d.get_q() # primer objeto en la lista all_querys
    domain_name_in_query = first_query.get_qname() # nombre de dominio por el cual preguntamos

    return str(domain_name_in_query), client_addr, dom_id
  
  def __search_ip_of_domain(cache: Cache, domain: str, addr: str) -> str:
    root_addr = '8.8.8.8'

    is_in_cache, ip = cache.search_cache(domain)
    if is_in_cache:
      print('Responde cache! ')
      return ip

    d1 = send_dns_message(domain, addr)
    d2 = DNSReply(d1)

    if d2.responds_with_ip:
      cache.update_cache((domain, d2.data))
      return d2.data
    
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

    cache = Cache()

    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dgram_socket.bind(('127.0.0.1', 5354))  # CAMBIAR PUERTO A 5353 ANTES DE ENTREGAR

    while True:

      domain_name, client_addr, dom_id = cls.__recv_domain_name_dns_msg(dgram_socket)
      links_in_request = parse_domain(domain_name)

      addr = '8.8.8.8'
      for domain in links_in_request:
        addr = cls.__search_ip_of_domain(cache, domain, addr)

      resp = DNSRecord(DNSHeader(id=dom_id, qr=1,aa=1,ra=1),
                       q=DNSQuestion(domain_name),
                       a=RR(domain_name,rdata=A(addr)))

      dgram_socket.sendto(bytes(resp.pack()), client_addr)

      print(domain_name, 'corresponde a la IP: ', addr)


if __name__ == "__main__":
  
  DNSResolver.run()
