import keyboard

event = keyboard.read_event()
print( event.event_type )
print( event.name )

