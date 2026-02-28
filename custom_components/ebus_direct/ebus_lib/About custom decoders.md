## Creating a custom decoder
ebus_direct provides for the use of custom decoders.  
A custom decoder receives as input the message returned by the ‘find’ command to ebusd (a string) and returns the decoded value of the param (a string). Optionally, the decoder can return `None` if the string cannot be parsed or does not provide a valid value for the param.    
The string passed to the decoder is the response from the f command to ebusd. Note that when `max_age` is specified, the find command is by default `f -vvv`. As the command to ebusd is formatted as `f -vvv {find_tag}`, it is possible to include in `find_tag` specifiers to affect the format of the command output. An example is `-h MsgId`, which will result in the find command returning the raw message for MsgId in hex, including the master part. This allows for instance parsing the data embedded both in the message master and slave parts, a feature not supported currently by ebusd.  
Note that, if the sensor is defined as numeric, a test that it is actually numeric and that the value fits in the range between min and max (if provided) is done after the custom decoding. If the test fails, the value is swallowed and `None` is returned.  
Note also that different sensors can get the value from the same message by using different custom decoders.  
Examples of common decoders are provided in the module custom_decoders.py. One is used to decode the unique format of the date used by Wolf BM-2 controller and alike units, a date format not presently supported by ebusd.  
### How to use a custom decoder
To use a custom decoder you need to:
* add the code in `custom_decoders.py` or create it in a separate module and import it in custom_decoders.py
* add an entry in DECODER_TABLE  
    "my_decoder": my_decoder,  
* in ebus_entities.yaml, add for the relevant sensor block(s)  
    decoder: my_decoder  
### Testing
It is recommended to test your newly developed custom decoder by using the standalone script as described in README and verify the correct behaviour before porting the code into your HA environment.
