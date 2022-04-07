from utilities import *
import socket
from dnslib import DNSRecord

class DNSResolver:

  def __recv_domain_name_dns_msg(socket: socket) -> str:

    data, _ = socket.recvfrom(4096)
    d = DNSRecord.parse(data)
    first_query = d.get_q() # primer objeto en la lista all_querys
    domain_name_in_query = first_query.get_qname() # nombre de dominio por el cual preguntamos

    return str(domain_name_in_query)

  @classmethod
  def run(cls) -> None:

    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dgram_socket.bind(('127.0.0.1', 5354))  # CAMBIAR PUERTO A 5353 ANTES DE ENTREGAR

    while True:

      domain_name = cls.__recv_domain_name_dns_msg(dgram_socket)
      links_in_request = parse_domain(domain_name)

      i = 0
      addr = '192.33.4.12'
      while i < len(links_in_request):

        curr_link = links_in_request[i]
        d = send_dns_message()



if __name__ == "__main__":
  
  DNSResolver.run()
