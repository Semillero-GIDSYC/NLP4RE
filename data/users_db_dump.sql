--
-- PostgreSQL database dump
--

\restrict NIIt5ENhmUm6IhPVqyGuqNO9fN0bhoVIuoDgiijxxqLQMp2PSuXmQirgH5JexPc

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.conversations DROP CONSTRAINT IF EXISTS fk_user_conv;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS fk_user;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS fk_role;
ALTER TABLE IF EXISTS ONLY public.messages DROP CONSTRAINT IF EXISTS fk_conv_msg;
DROP INDEX IF EXISTS public.flyway_schema_history_s_idx;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_username_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS user_roles_pkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_pkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_name_key;
ALTER TABLE IF EXISTS ONLY public.messages DROP CONSTRAINT IF EXISTS messages_pkey;
ALTER TABLE IF EXISTS ONLY public.flyway_schema_history DROP CONSTRAINT IF EXISTS flyway_schema_history_pk;
ALTER TABLE IF EXISTS ONLY public.conversations DROP CONSTRAINT IF EXISTS conversations_pkey;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.user_roles;
DROP TABLE IF EXISTS public.roles;
DROP TABLE IF EXISTS public.messages;
DROP TABLE IF EXISTS public.flyway_schema_history;
DROP TABLE IF EXISTS public.conversations;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: flyway_schema_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flyway_schema_history (
    installed_rank integer NOT NULL,
    version character varying(50),
    description character varying(200) NOT NULL,
    type character varying(20) NOT NULL,
    script character varying(1000) NOT NULL,
    checksum integer,
    installed_by character varying(100) NOT NULL,
    installed_on timestamp without time zone DEFAULT now() NOT NULL,
    execution_time integer NOT NULL,
    success boolean NOT NULL
);


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid NOT NULL,
    sender character varying(50) NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(50) NOT NULL
);


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    user_id uuid NOT NULL,
    role_id uuid NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.conversations (id, user_id, title, created_at) FROM stdin;
83b922dd-8469-47da-969f-4f7925029462	8e1b26e0-239d-45de-a94f-bdff5a6338da	el login del sistema debe ser segur...	2026-08-10 01:50:46.724076
3c8667fa-4f86-4e96-89ca-dae42d35dde7	8e1b26e0-239d-45de-a94f-bdff5a6338da	el sistema debe permitir al usuario...	2026-08-14 04:04:56.754212
3e206594-d94a-4be6-b087-df0916b5b2ab	8e1b26e0-239d-45de-a94f-bdff5a6338da	el sistema debe permitir al usuario...	2026-08-14 15:16:47.148656
412ef819-d0d0-4c61-b207-0af245482e87	cfec0f90-a589-463b-81c7-f3bbf7ae3464	Mi Requisito	2026-10-05 08:13:23.811487
7966ff2e-ddb8-42fa-aa04-7f99a6072a58	8e1b26e0-239d-45de-a94f-bdff5a6338da	el sistema debe tener un módulo par...	2026-10-05 08:31:13.398206
00d1c670-68c0-43e2-9477-7bb29773f259	8e1b26e0-239d-45de-a94f-bdff5a6338da	req funcional 001 el sistema debe t...	2026-10-05 22:15:57.760215
dd386afa-eaae-4f6c-87ed-2b9e956a2b3e	8e1b26e0-239d-45de-a94f-bdff5a6338da	req 001 el sistema debe poder dejar...	2026-10-05 22:19:32.706939
\.


--
-- Data for Name: flyway_schema_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.flyway_schema_history (installed_rank, version, description, type, script, checksum, installed_by, installed_on, execution_time, success) FROM stdin;
1	1	init	SQL	V1__init.sql	1231858817	admin	2026-08-05 05:05:49.119237	71	t
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.messages (id, conversation_id, sender, content, created_at) FROM stdin;
80a2ed49-d8cc-4453-9770-ebfeb10b74ee	83b922dd-8469-47da-969f-4f7925029462	USER	el login del sistema debe ser seguro	2026-08-10 01:50:46.838934
69de002f-bd5e-4c07-a583-95b4865f4958	83b922dd-8469-47da-969f-4f7925029462	AI	{"evaluation":{"VERIFIABILITY":{"score":1,"explanation":"El requisito menciona 'seguro' lo cual es subjetivo y requiere definición de métricas para su verificación."},"ATOMICITY":{"score":2,"explanation":"El requisito expresa una única idea: asegurar el login del sistema."},"AMBIGUITY":{"score":1,"explanation":"El término 'seguro' es ambiguo y requiere mayor especificidad. Se necesita definir qué criterios de seguridad se deben cumplir (ej., cifrado, autenticación multifactor)."},"COMPLETENESS":{"score":1,"explanation":"Falta especificar los mecanismos concretos para garantizar la seguridad del login (ej., tipo de autenticación, longitud mínima de contraseña, etc.)."},"TRACEABLE":{"score":0,"explanation":"El requisito no hace referencia a ningún caso de uso o identificador formal. Solo menciona 'el login del sistema' que es un término genérico."}},"feedback":{"suggestions":["Para mejorar la VERIFIABILITY (score 1), definir métricas específicas para 'seguro'. Por ejemplo: 'El login del sistema debe resistir ataques de fuerza bruta durante un período de X horas', o 'La contraseña mínima debe tener Y caracteres y incluir Z tipos de caracteres'.","Para mejorar el ATOMICITY (score 2), este requisito ya es lo suficientemente atomico. No se requiere cambio.","Para mejorar la AMBIGUITY (score 1), especificar los mecanismos de seguridad a implementar.  Ejemplo: 'El login del sistema debe utilizar autenticación multifactor basada en TOTP, con una contraseña mínima de 12 caracteres que incluya mayúsculas, minúsculas, números y símbolos'.","Para mejorar la COMPLETENESS (score 1), detallar los pasos para el proceso de login. Ejemplo: 'El sistema debe validar la entrada del usuario contra una lista negra de direcciones IP bloqueadas, implementar un CAPTCHA para prevenir ataques automatizados y registrar todos los intentos de inicio de sesión (éxitos y fallidos) en un registro de auditoría'.","Para mejorar el TRACEABLE (score 0), vincular este requisito a uno o más casos de uso específicos. Ejemplo: 'El login seguro es necesario para el caso de uso: Usuario - Iniciar Sesión al Sistema' o asignar un ID único al requisito, como LOGIN-001."],"improved_requirement":"El login del sistema debe cumplir con los siguientes criterios de seguridad: 1) Utilizar autenticación multifactor basada en TOTP. 2) La contraseña mínima debe tener 12 caracteres y contener al menos una mayúscula, minúscula, un número y un símbolo. 3) El sistema debe validar la entrada del usuario contra una lista negra de direcciones IP bloqueadas y aplicar un CAPTCHA para prevenir ataques automatizados. 4) Todos los intentos de inicio de sesión (éxitos y fallidos) deben ser registrados en un registro de auditoría con el ID LOGIN-001, vinculado al caso de uso Usuario - Iniciar Sesión al Sistema."}}	2026-08-10 01:54:38.493495
e0023415-f25a-4a05-920e-7e426cfe01ad	3c8667fa-4f86-4e96-89ca-dae42d35dde7	USER	el sistema debe permitir al usuario poder reservar un viaje indicando la fecha de inicio y ambas direcciones, inicio y destino(caso de uso 4)	2026-08-14 04:04:56.832662
4d5b7093-5d74-498e-967d-2c4bd9d7dd7e	3c8667fa-4f86-4e96-89ca-dae42d35dde7	AI	{"evaluation":{"VERIFIABILITY":{"score":1,"explanation":"El requisito describe acciones pero no especifica criterios medibles para determinar si el usuario puede reservar un viaje con la fecha y direcciones indicadas."},"ATOMICITY":{"score":2,"explanation":"El requisito se centra en una única acción: permitir al usuario reservar un viaje. No contiene elementos que lo dividan en partes independientes."},"AMBIGUITY":{"score":1,"explanation":"Aunque el requisito es relativamente claro, la frase 'indicando la fecha de inicio y ambas direcciones' podría ser mejorada para especificar formatos de fecha o tipos de direcciones aceptados. Se necesita más contexto sobre los requisitos de entrada."},"COMPLETENESS":{"score":1,"explanation":"Falta definir el resultado esperado de la reserva (ej., confirmación del viaje, error si no hay viajes disponibles). No especifica las condiciones bajo las cuales se puede reservar un viaje."},"TRACEABLE":{"score":1,"explanation":"El requisito hace referencia al caso de uso 4, pero no proporciona un identificador formal. Se podría mejorar la trazabilidad utilizando un código de caso de uso específico."}},"feedback":{"suggestions":["Para mejorar la VERIFIABILITY (score 1), se debe agregar un criterio medible: 'El sistema debe permitir al usuario reservar un viaje cuando la fecha de inicio y ambas direcciones sean válidas según el formato especificado en la sección X del manual del usuario.'","Para mejorar la ATOMICITY (score 2), dividir el requisito en dos: uno para la entrada de datos (fecha de inicio y direcciones) y otro para la reserva del viaje.","Para mejorar la AMBIGUITY (score 1), especificar los formatos aceptados para las fechas (ej., YYYY-MM-DD) y los tipos de direcciones permitidos (ej., formato postal estándar, coordenadas geográficas).  Además, definir si se requiere validación de direcciones.","Para mejorar la COMPLETENESS (score 1), agregar el resultado esperado: 'El sistema debe mostrar una confirmación del viaje con detalles como número de reserva, itinerario y datos del pasajero. Si no hay viajes disponibles para las fechas y destinos especificados, el sistema debe mostrar un mensaje de error claro.'","Para mejorar la TRACEABLE (score 1), reemplazar 'caso de uso 4' con un identificador único: 'CU-04 - Reserva de Viaje con Direcciones'."],"improved_requirement":"El sistema permite al usuario reservar un viaje especificando una fecha de inicio y ambas direcciones. La fecha de inicio debe ser en formato YYYY-MM-DD. Las direcciones deben ser de tipo postal estándar, siguiendo el formato [Especificar Formato]. El sistema valida la entrada para asegurar que la fecha sea válida y la dirección tiene un formato correcto.  Al completar la reserva, el sistema muestra una confirmación del viaje con número de reserva, itinerario y datos del pasajero. Si no hay viajes disponibles para las fechas y destinos especificados, el sistema muestra un mensaje de error claro indicando la razón. Este requisito se corresponde con el Caso de Uso CU-04 - Reserva de Viaje con Direcciones."}}	2026-08-14 04:08:46.415923
e990e818-cdf9-4e51-9a2f-089f017f1c4d	3e206594-d94a-4be6-b087-df0916b5b2ab	USER	el sistema debe permitir al usuario administrador gestionar los clientes de la empresa para así poder generar reportes (CU 07)	2026-08-14 15:16:47.267403
1ca8eb2f-df0b-45b2-b98b-298f07928dfa	3e206594-d94a-4be6-b087-df0916b5b2ab	AI	{"evaluation":{"VERIFIABILITY":{"score":1,"explanation":"El requisito describe una funcionalidad general ('gestionar los clientes') y no especifica criterios medibles para verificar si la gestión se realiza correctamente."},"ATOMICITY":{"score":1,"explanation":"El requisito combina dos acciones: 'gestionar' y 'generar reportes'. Podría dividirse en dos requisitos más específicos."},"AMBIGUITY":{"score":1,"explanation":"El término 'gestionar los clientes' es ambiguo. No especifica qué acciones de gestión se incluyen (creación, modificación, eliminación, etc.)."},"COMPLETENESS":{"score":0,"explanation":"Falta la condición de activación (qué tipo de usuarios pueden gestionar), la acción específica de gestión y el resultado esperado del reporte."},"TRACEABLE":{"score":1,"explanation":"El requisito hace referencia al caso de uso CU 07, pero no proporciona un identificador formal. Se menciona 'usuario administrador' que es un rol genérico."}},"feedback":{"suggestions":["Para VERIFIABILITY, definir criterios de aceptación claros para la gestión de clientes. Por ejemplo: 'El sistema debe permitir al administrador crear, modificar y eliminar registros de cliente con una precisión del 99%'.","Para ATOMICITY, dividir el requisito en dos: 1) 'El sistema debe permitir al usuario administrador crear, leer, actualizar y eliminar registros de clientes.' y 2) 'El sistema debe permitir al usuario administrador generar un reporte de clientes basado en criterios definidos (ej. por fecha de registro, tipo de cliente, etc.)'.","Para AMBIGUITY, especificar las acciones de gestión permitidas: 'El sistema debe permitir al administrador crear, modificar y eliminar registros de clientes, incluyendo la actualización de información personal, direcciones, datos de contacto y estado del cliente.'","Para COMPLETENESS, agregar detalles sobre el usuario que puede gestionar los clientes (ej. 'Solo usuarios con el rol de Administrador'), la acción específica de gestión (ej. 'El sistema debe permitir al administrador actualizar el campo 'estado' del cliente a 'Activo', 'Inactivo' o 'Pendiente') y el resultado esperado del reporte (ej. 'El reporte debe incluir una lista de clientes filtrados por fecha de registro, con sus datos personales y estado actual').","Para TRACEABLE, asignar un identificador único al requisito (ej. REQ-007) y definir roles específicos como 'Administrador' con atributos claros (ej. permisos de acceso a la gestión de clientes)."],"improved_requirement":"El sistema debe permitir que los usuarios con el rol de Administrador gestionen los registros de clientes. Esto incluye la creación, lectura, actualización y eliminación de registros de cliente, así como la modificación de campos como información personal, direcciones, datos de contacto y estado del cliente (Activo, Inactivo o Pendiente). El sistema debe generar un reporte de clientes basado en criterios definidos por el administrador (ej., fecha de registro, tipo de cliente), que incluya una lista de clientes filtrados con sus datos personales y estado actual.  El identificador único para este requisito es REQ-007."}}	2026-08-14 15:21:24.248663
2e37cc59-d396-449a-81a4-2e67bd29d884	412ef819-d0d0-4c61-b207-0af245482e87	USER	El sistema debe...	2026-10-05 08:13:33.445734
d0c4446a-182f-4d0a-892c-f64e300e685f	7966ff2e-ddb8-42fa-aa04-7f99a6072a58	USER	el sistema debe tener un módulo para poder hacer un volqueo masivo de datos que guarde los datos de las ventas por mes	2026-10-05 08:31:13.503707
40f82b46-ee7e-444c-b279-d183a05799c3	7966ff2e-ddb8-42fa-aa04-7f99a6072a58	AI	{"evaluation":{"VERIFIABILITY":{"score":0,"explanation":"El requisito usa términos subjetivos y no medibles como 'volqueo masivo de datos' y 'guarde los datos de las ventas por mes' sin definir métricas específicas, formato, destino o criterios de éxito, lo que impide una verificación objetiva. El contexto normativo (Contexto 2) sugiere la necesidad de 'check data integrity' y 'assure data privacy', lo que implica la existencia de criterios medibles que este requisito no proporciona."},"ATOMICITY":{"score":1,"explanation":"El requisito es mayormente atómico, describiendo una funcionalidad principal ('tener un módulo para hacer un volqueo masivo de datos'). Sin embargo, la cláusula 'que guarde los datos de las ventas por mes' introduce una idea secundaria que especifica el tipo de datos y la periodicidad del guardado, pudiendo considerarse una función o restricción separable del volqueo general."},"AMBIGUITY":{"score":0,"explanation":"El requisito es altamente ambiguo. Términos como 'módulo', 'volqueo masivo de datos' (qué es un volqueo, qué significa masivo, qué datos) y 'guarde los datos de las ventas por mes' (dónde, cómo, qué datos de ventas, por mes) tienen múltiples interpretaciones. El Contexto 3 de la ISO 29148 enfatiza la necesidad de un glosario para definir términos y evitar ambigüedades, lo cual este requisito no cumple."},"COMPLETENESS":{"score":0,"explanation":"Faltan elementos clave. No se especifica la condición de activación (cuándo o quién activa el volqueo). Aunque menciona la acción ('tener un módulo para hacer un volqueo masivo'), el resultado esperado ('que guarde los datos de las ventas por mes') es incompleto, ya que no define dónde se guardan, en qué formato, cómo se accede o qué sucede en caso de fallo. Al faltar la condición y ser el resultado implícito e incompleto, se considera que faltan dos o más elementos clave."},"TRACEABLE":{"score":0,"explanation":"El requisito no hace referencia a ningún actor, rol, caso de uso, regla de negocio o documento fuente mediante un identificador o código formal. El Contexto 1 de la ISO 29148 menciona la 'human systems integration' y la integración de 'human considerations', lo que implica la necesidad de vincular los requisitos a sus orígenes o stakeholders, algo que este requisito omite por completo."}},"feedback":{"suggestions":["Definir el formato de salida de los datos (ej. CSV, JSON) y la estructura de los campos para permitir una verificación objetiva del contenido.","Establecer métricas cuantitativas para el término 'masivo' (ej. número de registros, tiempo máximo de procesamiento) para que el requisito sea medible.","Especificar criterios de integridad de datos para el volcado (ej. que el número de registros volcados coincida con el origen) para asegurar la calidad de los datos.","Clarificar el término 'volqueo masivo de datos' especificando que se refiere a la exportación de un conjunto completo de datos de ventas de un período determinado.","Listar explícitamente los campos de datos de ventas que deben ser incluidos en el volcado para eliminar ambigüedades sobre el contenido.","Identificar el rol de usuario que puede iniciar la operación de volcado y el evento o la acción que lo desencadena.","Asignar un identificador único al requisito (ej. REQ-VENTAS-001) y vincularlo a un rol de usuario o caso de uso para mejorar su trazabilidad."],"improved_requirement":"REQ-VENTAS-001: El sistema debe permitir al Analista de Ventas generar y exportar un archivo consolidado con los datos de todas las transacciones de ventas completadas de un mes calendario específico. Este archivo debe estar en formato CSV, contener los campos [ID_Venta, Fecha, Producto, Cantidad, Precio_Unitario, Total_Venta, Cliente_ID], y ser accesible desde un directorio de red compartido ('/ventas/exportaciones/') para su descarga. El proceso de exportación debe ser iniciado manualmente por el Analista de Ventas y completarse en menos de 5 minutos para un volumen de hasta 100,000 registros de ventas, asegurando que el número de registros exportados coincida con el origen y que los datos mantengan su integridad."}}	2026-10-05 08:31:52.915466
82641787-0481-431f-8e83-77b30184b7f1	00d1c670-68c0-43e2-9477-7bb29773f259	USER	req funcional 001 el sistema debe tener un modulo para reservar un viaje via efecto o pse, y el chofer puede decidir si lo acepta o no	2026-10-05 22:15:57.921423
b5d19545-2945-4624-bd4e-5efb5af1f5f5	dd386afa-eaae-4f6c-87ed-2b9e956a2b3e	USER	req 001 el sistema debe poder dejar al usuario resevar un viaje via pse o efectivo y debe permitir que el chofer lo acepte o no	2026-10-05 22:19:32.749166
8d90a1bd-11aa-49ad-8e75-fe4f6a550972	dd386afa-eaae-4f6c-87ed-2b9e956a2b3e	AI	{"evaluation":{"VERIFIABILITY":{"score":1,"explanation":"El requisito describe acciones funcionales ('resevar un viaje', 'acepte o no') que son inherentemente verificables, pero carece de métricas específicas o condiciones de prueba claras (ej. tiempos de respuesta, tasas de éxito) para alcanzar un nivel 2. El contexto ISO proporcionado no aborda directamente la verificabilidad de requisitos funcionales."},"ATOMICITY":{"score":0,"explanation":"El requisito contiene dos ideas independientes unidas por la conjunción 'y': la capacidad del usuario para reservar un viaje y la capacidad del chofer para aceptarlo o rechazarlo. Estas deberían ser requisitos separados. El contexto ISO proporcionado no aborda directamente la atomicidad de los requisitos."},"AMBIGUITY":{"score":1,"explanation":"El requisito es mayormente claro, pero contiene un error tipográfico ('resevar' en lugar de 'reservar') y el término 'viaje' carece de contexto específico, lo que podría llevar a interpretaciones ligeramente diferentes sobre el tipo de servicio. El contexto ISO proporcionado no aborda directamente la ambigüedad de los términos en los requisitos."},"COMPLETENESS":{"score":1,"explanation":"El requisito describe las acciones del sistema ('resevar un viaje', 'acepte o no') pero omite la condición de activación explícita (cuándo ocurre la acción) y no detalla completamente los resultados o estados esperados después de cada acción (ej. qué sucede si el chofer rechaza). El contexto ISO proporcionado no aborda directamente la completitud de los requisitos en términos de condición, acción y resultado."},"TRACEABLE":{"score":1,"explanation":"El requisito menciona actores genéricos ('el usuario', 'el chofer') lo que permite una trazabilidad básica a roles, pero no incluye una referencia explícita y formal a un origen específico como un identificador de caso de uso (ej. UC-04) o un requisito de negocio (ej. BR-12). El contexto ISO proporcionado no aborda directamente la trazabilidad formal de los requisitos."}},"feedback":{"suggestions":["Dividir el requisito original en dos requisitos funcionales distintos: uno que describa la capacidad del usuario para reservar un servicio de transporte y otro que describa la capacidad del chofer para gestionar dicha solicitud, abordando así la atomicidad.","Corregir el error tipográfico 'resevar' a 'reservar'. Clarificar el término 'viaje' especificándolo como 'servicio de transporte' para eliminar ambigüedad.","Detallar las precondiciones para la reserva (ej. selección de origen/destino) y los post-estados esperados tras la acción del usuario (ej. generación de solicitud, confirmación provisional) para mejorar la completitud.","Incorporar métricas de rendimiento y éxito, como el tiempo máximo de respuesta del sistema para la confirmación de la reserva y la tasa de éxito esperada para las transacciones de pago, para aumentar la verificabilidad.","Asignar un identificador único y formal al requisito (ej. RF-001) y establecer un vínculo explícito a su origen, como un requisito de negocio o un caso de uso de nivel superior, para mejorar la trazabilidad."],"improved_requirement":"RF-001: El sistema debe permitir al usuario reservar un servicio de transporte, seleccionando un origen y destino, y eligiendo entre los métodos de pago PSE o efectivo. Tras la selección y confirmación, el sistema debe generar una solicitud de servicio y presentar una confirmación provisional al usuario en un plazo máximo de 3 segundos, con una tasa de éxito de transacción del 99% para PSE."}}	2026-10-05 22:22:31.08586
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, name) FROM stdin;
d8d0578b-1112-4653-bde1-bbbf043bff69	ROLE_USER
c880e1a7-d9b4-49a2-bd39-5c38ed0b4dd7	ROLE_ADMIN
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_roles (user_id, role_id) FROM stdin;
8e1b26e0-239d-45de-a94f-bdff5a6338da	d8d0578b-1112-4653-bde1-bbbf043bff69
cfec0f90-a589-463b-81c7-f3bbf7ae3464	d8d0578b-1112-4653-bde1-bbbf043bff69
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, email, password, created_at) FROM stdin;
8e1b26e0-239d-45de-a94f-bdff5a6338da	xlancet	crincones578@gmail.com	$2a$10$k.Cg9kkQp8wh6kKFqnphvOQXQ.YQjk1E80dEUaAIqpLC5Rd9YKjf.	2026-08-10 01:49:05.057898
cfec0f90-a589-463b-81c7-f3bbf7ae3464	carlosrs14	carlosrs14@test.com	$2a$10$GRHuBkwVtjwFGO5OtlP5IupSgrU9h7QSkUUm0HSgSyLUL5zaFbTN2	2026-10-05 08:12:44.773893
\.


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: flyway_schema_history flyway_schema_history_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flyway_schema_history
    ADD CONSTRAINT flyway_schema_history_pk PRIMARY KEY (installed_rank);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: flyway_schema_history_s_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX flyway_schema_history_s_idx ON public.flyway_schema_history USING btree (success);


--
-- Name: messages fk_conv_msg; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT fk_conv_msg FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: user_roles fk_role; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles fk_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: conversations fk_user_conv; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT fk_user_conv FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict NIIt5ENhmUm6IhPVqyGuqNO9fN0bhoVIuoDgiijxxqLQMp2PSuXmQirgH5JexPc

