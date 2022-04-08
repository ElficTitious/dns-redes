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

  @classmethod
  def run(cls) -> None:

    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dgram_socket.bind(('127.0.0.1', 5354))  # CAMBIAR PUERTO A 5353 ANTES DE ENTREGAR
    root_addr = '8.8.8.8'

    while True:

      domain_name, client_addr, dom_id = cls.__recv_domain_name_dns_msg(dgram_socket)
      links_in_request = parse_domain(domain_name)

      i = 0
      addr = root_addr
      curr_link = links_in_request[i]
      while i < len(links_in_request) - 1:

        d = send_dns_message(curr_link, addr)
        d = DNSReply(d)

        if d.responds_with_ip:
          i += 1
          curr_link = links_in_request[i]
          addr = d.data
        
        else:
          curr_link = d.data
          addr = root_addr
      
      d = send_dns_message(curr_link, addr)
      d = DNSReply(d)
      
      if not d.responds_with_ip:

        d = send_dns_message(d.data, root_addr)
        d = DNSReply(d)

      domain_ip = d.data

      resp = DNSRecord(DNSHeader(id=dom_id, qr=1,aa=1,ra=1),
                       q=DNSQuestion(domain_name),
                       a=RR(domain_name,rdata=A(domain_ip)))

      dgram_socket.sendto(bytes(resp.pack()), client_addr)

      print(domain_name, 'corresponde a la IP: ', domain_ip)



if __name__ == "__main__":
  
  DNSResolver.run()
