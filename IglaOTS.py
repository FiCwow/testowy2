def get_config():
    """
    Returns the configuration dictionary for IglaOTS.
    """
    return {
        # Game variables
        'square_size': 60,
        'application_architecture': 64,
        'collect_threshold': 0.85, # In pixels
        'client_name': "Tibia -", # If game 64 - 64Bit 32 - 32 Bit
 
        # Character Addresses
        'my_x_address': 0x019C6628,
        'my_x_address_offset': [0x510, 0x60],
        'my_x_type': 3,
        'my_y_address': 0x019C6628,
        'my_y_address_offset': [0x510, 0x60 + 0x04],
        'my_y_type': 3,
        'my_z_address': 0x019C6628,
        'my_z_address_offset': [0x510, 0x60 + 0x08],
        'my_z_type': 2,
        'my_stats_address': 0x019C6628,
        'my_hp_offset': [0xD8, 0X18],
        'my_hp_max_offset': [0xD8, 0X1C],
        'my_hp_type': 2,
        'my_mp_offset': [0xD8, 0X60],
        'my_mp_max_offset': [0xD8, 0X64],
        'my_mp_type': 2,
 
        # Target Addresses
        'attack_address': 0x019C6628,
        'attack_address_offset': [0x2C0, 0x2C],
        'my_attack_type': 3,
        'target_x_offset': 0x38,
        'target_x_type': 3,
        'target_y_offset': 0x3C,
        'target_y_type': 3,
        'target_z_offset': 0x40,
        'target_z_type': 2,
        'target_hp_offset': 0xE8,
        'target_hp_type': 1,
        'target_name_offset': 0xA8,
        'target_name_type': 6,

        # Battle List Addresses
        'battle_list_start': 0x019C6628,
        'battle_list_offset': [0x2C0],
        'battle_list_step': 0x110, # Distance between each creature in memory
        'battle_list_max_creatures': 1300,
        'battle_list_creature_id_offset': 0x8, # Offset from creature base to its ID
        'battle_list_creature_name_offset': 0xA8, # Offset from creature base to its name
        'battle_list_is_visible_offset': 0x18, # Offset to check if creature is visible on screen
    }