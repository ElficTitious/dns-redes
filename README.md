# DNS Ressolver

Semana 4 y 5 del Curso de Redes CC4303 FCFM

## Ejecución del DNS Resolver

```bash
pip install requirements.txt
python3 dns_resolver.py
```

## Estructura del código y funcionamiento del DNS Resolver

### Estructura

Se incluyen dos archivos de código, `utilities.py` y `dns_resolver.py`, donde el primero tiene todas las definiciones necesarias para el funcionamiento del Resolver, y el segundo tiene el Resolver _per se_.

### Funcionamiento del Resolver

Se desarrolla una clase estática `DNSResolver` con un método `run`, el cual debe ser llamado para ejecutar el resolver. El Resolver recibe consultas DNS desde un cliente (para testeo se usa `dig`) en localhost puerto 5353, esta consulta es parseada y se realizan todas las consultas necesarias para resolver la dirección correspondiente. Se aprovecha los resultados almacenando pares `(dominio, respuesta)` en un caché, el cual almacena las 10 consultas mas realizadas dentro de las últimas 100.

Es importante notar que muchas veces las respuestas corresponden a SOA o NS, por lo cual primero se resuelve la IP de aquellos antes de proseguir con la cadena de consultas.

Finalmente se retorna la respuesta a la misma dirección desde la cual se realizó la consulta.
