# powerbi-api-dax

Un script Python para demostrar el uso de la API REST de Power BI para hacer consultas DAX
https://powerbi.microsoft.com/es-es/blog/announcing-the-public-preview-of-power-bi-rest-api-support-for-dax-queries/

Requerimientos:
- Una licencia Pro de Power BI
- Regisitrar una aplicación Power BI en Azure utilizando esta página https://app.powerbi.com/embedsetup/AppOwnsData
- Luego de resgistrada la aplicación, obtener el ID de la misma para guardarla en la variable de entorno PBI_CLIENT_ID


Utiliza las siguientes variables del entorno:
- PBI_CLIENT_ID: ID de la aplicación registrada en Azure para aceeder a Power BI
- PBI_USER: Usuario para el servicio de Power BI
- PBI_PASSWORD: Contraseña para el servicio de Power BI
- PBI_DATASET_ID: ID del conjunto de datos Power BI contra el que se van a ejecutar las consultas DAX


Uso:
py dax.py [consulta_dax.dax] [-csv resultados.csv]

donde:
- consulta_dax.dax es la ruta a un fichero que contiene la consulta DAX.  Si no se pasa este parámetro se busca un fichero con el nombre dax_query.dax
- resultados.csv es la ruta a un fichero CSV donde se almacenan los resultados de la consulta DAX




