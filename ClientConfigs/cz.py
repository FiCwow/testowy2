def get_config():
    """
    Returns the configuration dictionary.
    """
    return {
    # Game variables
    'square_size': 0x3c,
    'application_architecture': 0x40,
    'collect_threshold': 0.85,
    'client_name': 'Tibia -',

    # Character Addresses
    'my_x_address': 0x19c6628,
    'my_x_address_offset': [0x510, 0x60],
    'my_x_type': 0x3,
    'my_y_address': 0x19c6628,
    'my_y_address_offset': [0x510, 0x64],
    'my_y_type': 0x3,
    'my_z_address': 0x19c6628,
    'my_z_address_offset': [0x510, 0x68],
    'my_z_type': 0x2,
    'my_stats_address': 0x19c6628,
    'my_hp_offset': [0xd8, 0x18],
    'my_hp_max_offset': [0xd8, 0x1c],
    'my_hp_type': 0x2,
    'my_mp_offset': [0xd8, 0x60],
    'my_mp_max_offset': [0xd8, 0x64],
    'my_mp_type': 0x2,
    'my_attack_type': 0x3,

    # Target Addresses
    'attack_address': 0x19c6628,
    'attack_address_offset': [0x2c0, 0x2c],
    'target_x_offset': 0x38,
    'target_x_type': 0x3,
    'target_y_offset': 0x3c,
    'target_y_type': 0x3,
    'target_z_offset': 0x40,
    'target_z_type': 0x2,
    'target_hp_offset': 0xe8,
    'target_hp_type': 0x1,
    'target_name_offset': 0xa8,
    'target_name_type': 0x6,
}
