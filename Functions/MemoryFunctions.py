import win32api
import win32con
import win32security
import Addresses
import ctypes as c


# Reads value from memory
def read_memory_address(address_read, offsets, option):
    try:
        address = c.c_void_p(Addresses.base_address + address_read + offsets)
        buffer_size = int(Addresses.application_architecture/8)
        buffer = c.create_string_buffer(buffer_size)
        result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, address, buffer, buffer_size, c.byref(c.c_size_t()))
        if not result:
            return None
        match option:
            case 1:
                return c.cast(buffer, c.POINTER(c.c_byte)).contents.value
            case 2:
                return c.cast(buffer, c.POINTER(c.c_short)).contents.value
            case 3:
                return c.cast(buffer, c.POINTER(c.c_int)).contents.value
            case 4:
                return c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value
            case 5:
                return c.cast(buffer, c.POINTER(c.c_double)).contents.value
            case 6:
                try:
                    decoded_value = buffer.value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case _:
                return bytes(buffer)
    except Exception as e:
        print('Memory Exception:', e)
        return None


def read_pointer_address(address_read, offsets, option):
    try:
        address = c.c_void_p(Addresses.base_address + address_read)
        buffer_size = int(Addresses.application_architecture/8)
        buffer = c.create_string_buffer(buffer_size)
        for offset in offsets:
            result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, address, buffer, buffer_size, c.byref(c.c_size_t()))
            if not result:
                return None
            if buffer_size == 4:
                address = c.c_void_p(c.cast(buffer, c.POINTER(c.c_int)).contents.value + offset)
            else:
                address = c.c_void_p(c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value + offset)
        result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, address, buffer, buffer_size, c.byref(c.c_size_t()))
        if not result:
            return None
        match option:
            case 1:
                return c.cast(buffer, c.POINTER(c.c_byte)).contents.value
            case 2:
                return c.cast(buffer, c.POINTER(c.c_short)).contents.value
            case 3:
                return c.cast(buffer, c.POINTER(c.c_int)).contents.value
            case 4:
                return c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value
            case 5:
                return c.cast(buffer, c.POINTER(c.c_double)).contents.value
            case 6:
                try:
                    decoded_value = buffer.value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case _:
                return bytes(buffer)
    except Exception as e:
        print('Pointer Exception:', e)
        return None


def read_targeting_status():
    attack = read_pointer_address(Addresses.attack_address, Addresses.attack_address_offset, Addresses.my_attack_type)
    return attack


def read_my_stats():
    current_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_offset, Addresses.my_hp_type)
    current_max_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_max_offset, Addresses.my_hp_type)
    current_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_offset, Addresses.my_mp_type)
    current_max_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_max_offset, Addresses.my_mp_type)
    return current_hp, current_max_hp, current_mp, current_max_mp

def read_hp():
    """Reads and returns the character's current and max HP."""
    hp, max_hp, _, _ = read_my_stats()
    return hp, max_hp

def read_mp():
    """Reads and returns the character's current and max MP."""
    _, _, mp, max_mp = read_my_stats()
    return mp, max_mp

def read_character_speed():
    """Reads and returns the character's current speed."""
    speed = read_pointer_address(Addresses.my_stats_address, Addresses.my_speed_offset, Addresses.my_speed_type)
    return speed if speed is not None else 0


def read_my_wpt():
    x = read_pointer_address(Addresses.my_x_address, Addresses.my_x_address_offset, Addresses.my_x_type)
    y = read_pointer_address(Addresses.my_y_address, Addresses.my_y_address_offset, Addresses.my_y_type)
    z = read_pointer_address(Addresses.my_z_address, Addresses.my_z_address_offset, Addresses.my_z_type)
    return x, y, z


def read_target_info():
    target_base_ptr = read_pointer_address(Addresses.attack_address, Addresses.attack_address_offset, 4)
    if not target_base_ptr:
        return None, None, None, None, None
    target_x = read_memory_address(target_base_ptr - Addresses.base_address, Addresses.target_x_offset, Addresses.target_x_type)
    target_y = read_memory_address(target_base_ptr - Addresses.base_address, Addresses.target_y_offset, Addresses.target_y_type)
    target_z = read_memory_address(target_base_ptr - Addresses.base_address, Addresses.target_z_offset, Addresses.target_z_type)
    target_name = read_memory_address(target_base_ptr - Addresses.base_address, Addresses.target_name_offset, Addresses.target_name_type)
    target_hp = read_memory_address(target_base_ptr - Addresses.base_address, Addresses.target_hp_offset, Addresses.target_hp_type)
    return target_x, target_y, target_z, target_name, target_hp

def read_battle_list():
    """Reads the battle list and returns a list of dictionaries, each representing a creature."""
    creatures = []
    if not all([Addresses.battle_list_start, Addresses.battle_list_offset, Addresses.battle_list_step, Addresses.battle_list_max_creatures, Addresses.battle_list_is_visible_offset]):
        return creatures

    # First, read the pointer to the start of the battle list
    battle_list_base_ptr = read_pointer_address(Addresses.battle_list_start, Addresses.battle_list_offset, 4) # 4 = Long (pointer)
    if not battle_list_base_ptr:
        return creatures
    
    for i in range(Addresses.battle_list_max_creatures):
        # The address of each creature is relative to the start of the battle list
        creature_base_address = battle_list_base_ptr + (i * Addresses.battle_list_step)

        # Read creature ID to check if the slot is valid
        creature_id = read_memory_address(creature_base_address - Addresses.base_address, Addresses.battle_list_creature_id_offset, 3)
        is_visible = read_memory_address(creature_base_address - Addresses.base_address, Addresses.battle_list_is_visible_offset, 1)

        if creature_id is None or creature_id == 0 or is_visible == 0:
            continue

        creature_name = read_memory_address(creature_base_address - Addresses.base_address, Addresses.battle_list_creature_name_offset, 6)

        if creature_name:
            creatures.append({
                'id': creature_id,
                'name': creature_name,
            })
    return creatures


def enable_debug_privilege_pywin32():
    try:
        hToken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
        )
        privilege_id = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME) # type: ignore
        win32security.AdjustTokenPrivileges(hToken, 0, [(privilege_id, win32con.SE_PRIVILEGE_ENABLED)]) # type: ignore
        return True
    except Exception as e:
        print("Error:", e)
        return False
