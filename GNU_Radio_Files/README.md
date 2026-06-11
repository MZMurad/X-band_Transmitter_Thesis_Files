# GNU Radio
The above two folders contain the flow graphs for a BPSK TX/RX that was used during this project's testing
The second folder contains a differential QPSK TX/RX flow graphs that were used in this project's testing

These files were made with the LimeSDR Mini 2

To use the files:
- After cloning the git, within each TX and RX flow graph there is either a file source or a file sink
- Each of these blocks must be given a path to a source file (png, jpeg, or text) and a sink file
- The sink file will always be overwritten, make sure the sink file has the same extention as the source file
- Before running the graphs on a full system ensure that you can connect two SDRs with a cable (TX -> RX) and that the files are operational without any hardware in the loop

Some trouble shooting tips
- A lot of the time it is helpful to understand what each block does, make sure you read the GNU Wiki. The wiki also has examples that these files are based on.
- Make sure the gain of the TX and RX stages are in order, the files here have the gains used with hardware in the loop
- The bandwidth of the FLL block and costas loops are very important for synchonization. If you suspect there might be some synchonizing issues it is a good idea to start there
- The Access code correlation block has a threshold value that is set to 0 meaning that the block will only trigger "correct" if there are no bit errors, this is useful but depending on the system in between the SDRs may need to be increased.
