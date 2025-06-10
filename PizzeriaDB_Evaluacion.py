# -*- coding: utf-8 -*-
import pyodbc
from datetime import datetime
# --- CONFIGURACIÓN DE LA CONEXIÓN ---

SERVER_NAME = 'WIN-170IUCRPJ9H\SQLEXPRESS'
DATABASE_NAME = 'PizzeriaDB'
# Cadena de conexión
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER_NAME};"
    f"DATABASE={DATABASE_NAME};"
    f"Trusted_Connection=yes;"
)

# --- FUNCIONES AUXILIARES ---
def print_results(cursor, description="Resultados de la consulta"):
    """Función para imprimir de forma ordenada los resultados de cualquier consulta."""
    print(f"\n--- {description} ---")
    try:
        columns = [column[0] for column in cursor.description]
        header = " | ".join(f"{col: <20}" for col in columns)
        print(header)
        print("-" * len(header))
        
        rows = cursor.fetchall()
        if not rows:
            print("La consulta no devolvió resultados.")
            return False
        else:
            for row in rows:
                row_str = " | ".join(f"{str(item): <20}" for item in row)
                print(row_str)
            print("-" * len(header))
            return True
    except pyodbc.Error as ex:
        print(f"Error al procesar los resultados: {ex}")
        return False

# --- SECCIÓN DE CONSULTAS ESPECIALES ---
def run_special_queries(cursor):
    """Maneja el submenú de consultas especiales."""
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    while True:
        print("\n--- MENÚ DE CONSULTAS ESPECIALES ---")
        print("1. Top 3 Clientes con más pedidos")
        print("2. Pizzas más populares (ordenadas por demanda)")
        print("3. Pedidos realizados en uno o varios meses")
        print("4. Ingredientes extra más populares")
        print("5. Volver al menú principal")
        
        choice = input("Selecciona una consulta (1-5): ")

        if choice == '1':
            sql = "SELECT TOP 3 C.ID_Cliente, C.Nombre, C.Apellido, COUNT(P.ID_Pedido) AS TotalPedidos FROM Cliente AS C JOIN Pedido AS P ON C.ID_Cliente = P.ID_Cliente GROUP BY C.ID_Cliente, C.Nombre, C.Apellido ORDER BY TotalPedidos DESC;"
            cursor.execute(sql)
            print_results(cursor, "Top 3 Clientes con más pedidos")
        elif choice == '2':
            sql = "SELECT P.Nombre_Pizza, COUNT(DP.ID_Pizza_Menu) AS VecesPedida FROM DetallePedido AS DP JOIN Pizza AS P ON DP.ID_Pizza_Menu = P.ID_Pizza GROUP BY P.Nombre_Pizza ORDER BY VecesPedida DESC;"
            cursor.execute(sql)
            print_results(cursor, "Pizzas ordenadas por demanda")
        elif choice == '3':
            selected_months = []
            while True:
                try:
                    print("\nSelecciona un mes para agregar a tu consulta:")
                    for i, mes in enumerate(meses):
                        print(f"{i+1}. {mes}")
                    
                    num_mes = int(input("Ingresa el número del mes (1-12): "))
                    
                    if 1 <= num_mes <= 12:
                        if num_mes not in selected_months:
                            selected_months.append(num_mes)
                            print(f"✅ '{meses[num_mes-1]}' ha sido agregado a la consulta.")
                        else:
                            print(f"'{meses[num_mes-1]}' ya estaba en la lista.")
                    else:
                        print("Número de mes no válido.")

                except ValueError:
                    print("Debes ingresar un número.")

                another_month = input("\n¿Deseas agregar otro mes a la consulta? (s/n): ").lower()
                if another_month != 's':
                    break

            if selected_months:
                placeholders = ','.join(['?'] * len(selected_months))
                sql = f"SELECT ID_Pedido, ID_Cliente, Fecha_Hora_Pedido, Total_Pedido FROM Pedido WHERE MONTH(Fecha_Hora_Pedido) IN ({placeholders});"
                
                month_names = [meses[m-1] for m in sorted(selected_months)]
                description = f"Pedidos en los meses de {', '.join(month_names)}"
                
                cursor.execute(sql, selected_months)
                print_results(cursor, description)
            else:
                print("\nNo se seleccionó ningún mes para la consulta.")

        elif choice == '4':
            sql = "SELECT TOP 5 I.Nombre_Ingrediente, COUNT(PIP.ID_Ingrediente) AS Frecuencia FROM Pizza_Ingrediente_Personalizado AS PIP JOIN Ingrediente AS I ON PIP.ID_Ingrediente = I.ID_Ingrediente GROUP BY I.Nombre_Ingrediente ORDER BY Frecuencia DESC;"
            cursor.execute(sql)
            print_results(cursor, "Ingredientes extra más populares")
        elif choice == '5':
            break
        else:
            print("Opción no válida.")
        
        if choice in ['1', '2', '3', '4']:
             input("\nPresiona Enter para continuar...")


# --- SECCIÓN DE OPERACIONES ---

def create_new_client(cnxn, cursor, show_title=True):
    """Guía la creación de un nuevo cliente y devuelve su ID si tiene éxito."""
    if show_title:
        print("\n--- Creación de Nuevo Cliente ---")
    try:
        # MEJORA: Permitir cancelar en cualquier paso
        nombre = input("Nombre del cliente (o escriba 'cancelar' para salir): ")
        if nombre.lower() == 'cancelar': return None
        apellido = input("Apellido del cliente (o escriba 'cancelar' para salir): ")
        if apellido.lower() == 'cancelar': return None
        telefono = input("Teléfono (único) (o escriba 'cancelar' para salir): ")
        if telefono.lower() == 'cancelar': return None
        email = input("Email (único, opcional) (o escriba 'cancelar' para salir): ")
        if email.lower() == 'cancelar': return None
        direccion = input("Dirección (o escriba 'cancelar' para salir): ")
        if direccion.lower() == 'cancelar': return None
        
        sql = "INSERT INTO Cliente (Nombre, Apellido, Telefono, Email, Direccion_Completa) OUTPUT INSERTED.ID_Cliente VALUES (?, ?, ?, ?, ?)"
        params = (nombre, apellido, telefono, email if email else None, direccion)
        
        new_client_id = cursor.execute(sql, params).fetchval()
        cnxn.commit()
        
        print(f"\n✅ ¡Cliente '{nombre} {apellido}' creado con éxito! (ID: {new_client_id})")
        return new_client_id
        
    except pyodbc.IntegrityError:
        print("\nERROR: No se pudo crear el cliente. El teléfono o email ya existen.")
        return None
    except pyodbc.Error as ex:
        print(f"\nOcurrió un error inesperado: {ex}")
        return None

def create_new_order(cnxn, cursor):
    """Guía al usuario para crear un pedido completo."""
    print("\n--- Creación de un Nuevo Pedido ---")
    
    id_cliente = None
    while True:
        is_new_client = input("¿El pedido es para un cliente nuevo? (s/n): ").lower()
        if is_new_client == 's':
            id_cliente = create_new_client(cnxn, cursor, show_title=False)
            if id_cliente is not None:
                break
            else:
                print("Creación de cliente cancelada.")
                return # Salir si la creación del cliente se cancela
        elif is_new_client == 'n':
            if not print_results(cursor.execute("SELECT ID_Cliente, Nombre, Apellido FROM Cliente"), "Clientes Disponibles"):
                return
            try:
                id_cliente_str = input("Ingresa el ID del cliente que realiza el pedido (o 0 para cancelar): ")
                id_cliente = int(id_cliente_str)
                if id_cliente == 0:
                    print("Selección de cliente cancelada.")
                    return
                if cursor.execute("SELECT 1 FROM Cliente WHERE ID_Cliente = ?", id_cliente).fetchone():
                    break
                else:
                    print("ID de cliente no existe. Inténtalo de nuevo.")
            except ValueError:
                print("ID de cliente no válido.")
        else:
            print("Opción no válida. Por favor, responde 's' o 'n'.")
            
    if id_cliente is None:
        print("No se pudo definir un cliente. Pedido cancelado.")
        return

    carrito = []
    total_pedido = 0.0
    while True:
        if not print_results(cursor.execute("SELECT ID_Pizza, Nombre_Pizza, Precio_Base_Pizza FROM Pizza WHERE Disponible = 1"), "Menú de Pizzas"):
            return
        try:
            id_pizza = int(input("Ingresa el ID de la pizza a agregar (o 0 para terminar): "))
            if id_pizza == 0: break
            
            cursor.execute("SELECT Precio_Base_Pizza FROM Pizza WHERE ID_Pizza=?", id_pizza)
            row = cursor.fetchone()
            if not row:
                print("ID de pizza no válido.")
                continue
            
            precio_unitario = float(row[0])
            cantidad = int(input(f"Cantidad de esta pizza: "))

            extras = []
            while True:
                add_extra = input("¿Deseas agregar un ingrediente extra a esta pizza? (s/n): ").lower()
                if add_extra == 'n': break
                if add_extra == 's':
                    if not print_results(cursor.execute("SELECT ID_Ingrediente, Nombre_Ingrediente, Precio_Adicional_Ingrediente FROM Ingrediente WHERE Precio_Adicional_Ingrediente > 0"), "Ingredientes Extra Disponibles"):
                        break
                    try:
                        id_ingrediente = int(input("Ingresa el ID del ingrediente extra (o 0 para terminar con esta pizza): "))
                        if id_ingrediente == 0: break
                        cursor.execute("SELECT Precio_Adicional_Ingrediente FROM Ingrediente WHERE ID_Ingrediente=?", id_ingrediente)
                        extra_row = cursor.fetchone()
                        if extra_row:
                            precio_unitario += float(extra_row[0])
                            extras.append(id_ingrediente)
                            print("Ingrediente añadido.")
                        else:
                            print("ID de ingrediente no válido.")
                    except ValueError:
                        print("Entrada no válida.")
            
            subtotal = precio_unitario * cantidad
            carrito.append({'id_pizza': id_pizza, 'cantidad': cantidad, 'precio_unitario': precio_unitario, 'subtotal': subtotal, 'extras': extras})
            total_pedido += subtotal
            print(f"\nSubtotal actual del pedido: ${total_pedido:.2f}")

        except ValueError:
            print("Entrada no válida. Por favor, ingresa números.")
    
    if not carrito:
        print("No se agregaron pizzas. Pedido cancelado.")
        return
        
    direccion_entrega = input("Ingresa la dirección de entrega: ")
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    for i, mes in enumerate(meses):
        print(f"{i+1}. {mes}")
    try:
        num_mes = int(input("Selecciona el mes del pedido (1-12): "))
        if not 1 <= num_mes <= 12: raise ValueError()
        
        now = datetime.now()
        fecha_pedido = datetime(now.year, num_mes, now.day, now.hour, now.minute, now.second)

    except ValueError:
        print("Mes no válido. Pedido cancelado.")
        return

    try:
        sql_pedido = "INSERT INTO Pedido (ID_Cliente, Fecha_Hora_Pedido, Direccion_Entrega_Pedido, Total_Pedido) VALUES (?, ?, ?, ?);"
        cursor.execute(sql_pedido, id_cliente, fecha_pedido, direccion_entrega, total_pedido)
        id_pedido_nuevo = cursor.execute("SELECT @@IDENTITY AS NewID;").fetchval()
        
        for item in carrito:
            sql_detalle = "INSERT INTO DetallePedido (ID_Pedido, ID_Pizza_Menu, Cantidad, Precio_Unitario_Pizza_Personalizada, Subtotal_Detalle) VALUES (?, ?, ?, ?, ?);"
            cursor.execute(sql_detalle, id_pedido_nuevo, item['id_pizza'], item['cantidad'], item['precio_unitario'], item['subtotal'])
            id_detalle_nuevo = cursor.execute("SELECT @@IDENTITY AS NewID;").fetchval()
            
            for extra_id in item['extras']:
                sql_extra = "INSERT INTO Pizza_Ingrediente_Personalizado (ID_DetallePedido, ID_Ingrediente) VALUES (?, ?);"
                cursor.execute(sql_extra, id_detalle_nuevo, extra_id)
        
        cnxn.commit()
        print("\n✅ ¡Pedido creado exitosamente en la base de datos!")
        print(f"ID del nuevo pedido: {id_pedido_nuevo}, Total: ${total_pedido:.2f}")

    except pyodbc.Error as ex:
        cnxn.rollback()
        print(f"\n❌ Ocurrió un error al guardar el pedido. Se revirtieron los cambios. Error: {ex}")

# --- SECCIÓN DE MANTENIMIENTO ---

def add_new_pizza(cnxn, cursor):
    """Guía la creación de una nueva pizza."""
    print("\n--- Agregar Nueva Pizza ---")
    try:
        nombre = input("Nombre de la pizza (o escriba 'cancelar' para salir): ")
        if nombre.lower() == 'cancelar': return
        desc = input("Descripción (o escriba 'cancelar' para salir): ")
        if desc.lower() == 'cancelar': return
        precio_str = input("Precio base (o escriba 'cancelar' para salir): ")
        if precio_str.lower() == 'cancelar': return
        precio = float(precio_str)
        
        sql = "INSERT INTO Pizza (Nombre_Pizza, Descripcion_Pizza, Precio_Base_Pizza) VALUES (?, ?, ?)"
        cursor.execute(sql, nombre, desc, precio)
        cnxn.commit()
        print(f"\n✅ ¡Pizza '{nombre}' agregada con éxito!")
    except pyodbc.IntegrityError:
        print("\nERROR: Ya existe una pizza con ese nombre.")
    except (ValueError, TypeError):
        print("\nError: El precio debe ser un número válido.")
    except pyodbc.Error as ex:
        print(f"\nOcurrió un error: {ex}")

def add_new_ingredient(cnxn, cursor):
    """Guía la creación de un nuevo ingrediente."""
    print("\n--- Agregar Nuevo Ingrediente ---")
    try:
        nombre = input("Nombre del ingrediente (o escriba 'cancelar' para salir): ")
        if nombre.lower() == 'cancelar': return
        precio_str = input("Precio adicional (o escriba 'cancelar' para salir): ")
        if precio_str.lower() == 'cancelar': return
        precio = float(precio_str)
        tipo = input("Tipo de ingrediente (Ej: Extra Queso) (o escriba 'cancelar' para salir): ")
        if tipo.lower() == 'cancelar': return
        
        sql = "INSERT INTO Ingrediente (Nombre_Ingrediente, Precio_Adicional_Ingrediente, Tipo_Ingrediente) VALUES (?, ?, ?)"
        cursor.execute(sql, nombre, precio, tipo)
        cnxn.commit()
        print(f"\n✅ ¡Ingrediente '{nombre}' agregado con éxito!")
    except pyodbc.IntegrityError:
        print("\nERROR: Ya existe un ingrediente con ese nombre.")
    except (ValueError, TypeError):
        print("\nError: El precio debe ser un número válido.")
    except pyodbc.Error as ex:
        print(f"\nOcurrió un error: {ex}")

def handle_maintenance(cnxn, cursor):
    """Submenú para elegir qué tabla modificar."""
    while True:
        print("\n--- Mantenimiento de Registros ---")
        print("¿Qué tabla deseas modificar?")
        print("1. Cliente")
        print("2. Pizza")
        print("3. Ingrediente")
        print("4. Volver al Menú Principal")
        
        choice = input("Selecciona una tabla (1-4): ")
        
        if choice == '1':
            update_delete_menu(cnxn, cursor, 'Cliente', 'ID_Cliente')
        elif choice == '2':
            update_delete_menu(cnxn, cursor, 'Pizza', 'ID_Pizza')
        elif choice == '3':
            update_delete_menu(cnxn, cursor, 'Ingrediente', 'ID_Ingrediente')
        elif choice == '4':
            break
        else:
            print("Opción no válida.")

def update_delete_menu(cnxn, cursor, table_name, pk_name):
    """Menú genérico para CRUD en una tabla específica."""
    while True:
        print(f"\n--- Modificando tabla: {table_name} ---")
        print("1. Agregar nuevo registro")
        print("2. Actualizar un registro existente")
        print("3. Borrar un registro existente")
        print("4. Volver al menú de mantenimiento")

        choice = input("Selecciona una operación (1-4): ")

        if choice == '1': # AGREGAR
            if table_name == 'Cliente':
                create_new_client(cnxn, cursor)
            elif table_name == 'Pizza':
                add_new_pizza(cnxn, cursor)
            elif table_name == 'Ingrediente':
                add_new_ingredient(cnxn, cursor)
        
        elif choice == '2': # ACTUALIZAR
            print(f"\n--- Actualizar en '{table_name}' ---")
            if not print_results(cursor.execute(f"SELECT * FROM {table_name}"), f"Registros en {table_name}"):
                continue
            try:
                pk_value_str = input(f"Ingresa el {pk_name} del registro a actualizar (o 0 para cancelar): ")
                pk_value = int(pk_value_str)
                if pk_value == 0: continue

                if table_name == 'Cliente':
                    while True:
                        print("\n¿Qué campo del cliente deseas actualizar?")
                        print("1. Nombre | 2. Apellido | 3. Teléfono | 4. Email | 5. Dirección | 6. Cancelar")
                        field_choice = input("Selecciona un campo: ")
                        if field_choice == '1': field_to_update = 'Nombre'
                        elif field_choice == '2': field_to_update = 'Apellido'
                        elif field_choice == '3': field_to_update = 'Telefono'
                        elif field_choice == '4': field_to_update = 'Email'
                        elif field_choice == '5': field_to_update = 'Direccion_Completa'
                        elif field_choice == '6': break
                        else:
                            print("Opción no válida.")
                            continue
                        
                        new_value = input(f"Ingresa el nuevo valor para '{field_to_update}' (o escriba 'cancelar'): ")
                        if new_value.lower() == 'cancelar': break
                        sql = f"UPDATE Cliente SET {field_to_update} = ? WHERE ID_Cliente = ?"
                        params = (new_value, pk_value)
                        break
                else: # Lógica para Pizza e Ingrediente
                    if table_name == 'Pizza':
                        new_value_str = input("Ingresa el nuevo precio base (o escriba 'cancelar'): ")
                        if new_value_str.lower() == 'cancelar': continue
                        new_value = float(new_value_str)
                        sql = f"UPDATE Pizza SET Precio_Base_Pizza = ? WHERE ID_Pizza = ?"
                    elif table_name == 'Ingrediente':
                        new_value_str = input("Ingresa el nuevo precio adicional (o escriba 'cancelar'): ")
                        if new_value_str.lower() == 'cancelar': continue
                        new_value = float(new_value_str)
                        sql = f"UPDATE Ingrediente SET Precio_Adicional_Ingrediente = ? WHERE ID_Ingrediente = ?"
                    params = (new_value, pk_value)
                
                if 'sql' in locals() and 'params' in locals():
                    print(f"\nTabla '{table_name}' ANTES de la actualización:")
                    print_results(cursor.execute(f"SELECT * FROM {table_name} WHERE {pk_name} = ?", pk_value))
                    cursor.execute(sql, params)
                    if cursor.rowcount > 0:
                        cnxn.commit()
                        print("\n¡Actualización completada!")
                    else:
                        print("\nNo se encontró ningún registro con ese ID.")
                    print(f"Tabla '{table_name}' DESPUÉS de la actualización:")
                    print_results(cursor.execute(f"SELECT * FROM {table_name} WHERE {pk_name} = ?", pk_value))

            except (ValueError, TypeError):
                print("\nError: Entrada no válida.")
            except pyodbc.Error as ex:
                print(f"\nOcurrió un error: {ex}")
        
        elif choice == '3': # BORRAR
            print(f"\n--- Borrar en '{table_name}' ---")
            if not print_results(cursor.execute(f"SELECT * FROM {table_name}"), f"Registros en {table_name}"):
                continue
            try:
                pk_value_str = input(f"Ingresa el {pk_name} del registro a borrar (o 0 para cancelar): ")
                pk_value = int(pk_value_str)
                if pk_value == 0: continue

                print(f"\nTabla '{table_name}' ANTES del intento de borrado:")
                print_results(cursor.execute(f"SELECT * FROM {table_name}"))

                sql = f"DELETE FROM {table_name} WHERE {pk_name} = ?"
                cursor.execute(sql, pk_value)
                
                if cursor.rowcount > 0:
                    cnxn.commit()
                    print("\n¡Registro eliminado exitosamente!")
                else:
                    print("\nNo se encontró ningún registro con ese ID.")
                
                print(f"Tabla '{table_name}' DESPUÉS del intento de borrado:")
                print_results(cursor.execute(f"SELECT * FROM {table_name}"))

            except pyodbc.IntegrityError:
                print("\n❌ ERROR DE ELIMINACIÓN: No se puede eliminar este registro.")
                print("Motivo: Otros datos en la base de datos dependen de él (ej: un cliente con pedidos, una pizza en un pedido).")
            except ValueError:
                print("\nError: El ID debe ser un número.")
            except pyodbc.Error as ex:
                print(f"\nOcurrió un error inesperado: {ex}")
        
        elif choice == '4':
            break
        else:
            print("Opción no válida.")
        input("\nPresiona Enter para continuar...")


# --- FUNCIÓN PRINCIPAL ---
def main():
    """Función principal que maneja la conexión y el menú principal."""
    cnxn = None
    try:
        cnxn = pyodbc.connect(conn_str)
        cursor = cnxn.cursor()
        print("¡Conexión a la base de datos PizzeriaDB establecida con éxito! ✅")

        while True:
            print("\n============ MENÚ PRINCIPAL ============")
            print("1. Ver todas las tablas")
            print("2. Crear un nuevo Pedido completo")
            print("3. Consultas Especiales")
            print("4. Mantenimiento de Registros")
            print("5. Salir")
            
            choice = input("Selecciona una opción (1-5): ")

            if choice == '1':
                print("\nCargando todas las tablas...")
                tables = ['Cliente', 'Pizza', 'Ingrediente', 'Pedido', 'DetallePedido', 'Pizza_Ingrediente_Personalizado']
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    if print_results(cursor, f"Contenido de la tabla: {table}"):
                        input("Presiona Enter para ver la siguiente tabla...")
                    else:
                        print(f"No hay datos en la tabla {table}.")
                        input("Presiona Enter para continuar...")
                        
            elif choice == '2':
                create_new_order(cnxn, cursor)
            elif choice == '3':
                run_special_queries(cursor)
            elif choice == '4':
                handle_maintenance(cnxn, cursor)
            elif choice == '5':
                print("Cerrando conexión. ¡Hasta luego! 👋")
                break
            else:
                print("Opción no válida. Por favor, elige una opción del 1 al 5.")
    
    except pyodbc.Error as ex:
        print("\n*** ERROR DE CONEXIÓN A LA BASE DE DATOS *** ❌")
        print(f"No se pudo conectar a '{SERVER_NAME}'. Verifica la configuración.")
        print(ex)

    finally:
        if cnxn:
            cnxn.close()

# Ejecutar el programa
if __name__ == '__main__':
    main()
