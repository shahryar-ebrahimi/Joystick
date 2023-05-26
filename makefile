default: showrun gui


gui:
	python gui.py

showrun:
	@echo "For documentation, use:"
	@echo " make doc"
	@echo ""
	@echo "To run use:"
	@echo "	python main.py {SUBJECT} {SCHEDULE_FILE} {CALIB_FILE}"
	@echo ""
	@echo "For a dummy run (random feedback):"
	@echo "	python dummyrun.py {SUBJECT} {SCHEDULE_FILE} {CALIB_FILE} [scannersounds]"
	@echo ""
	@echo "If you don't give these parameters on the command-line the script will ask you for them."
	@echo "You can also use 'make run' to start without command-line options"
	@echo ""
	@echo "To make subject instructions, use 'make instructions' or 'make instructpdf'"

run:
	python main.py

clean:
	rm -f ./data/calib_test.txt ./data/test*.dat
	rm -f joystick-event
	rm -f readme.html
	rm -f *.pyc
	rm -f subject_instructions.html subject_instructions.pdf
	rm -f .lastcalib.txt


doc: readme.html
	xdg-open readme.html

readme.html: readme.md
	pandoc -f markdown -t html readme.md -c fonts/github-pandoc.css -s -o readme.html

subject_instructions.html: subject_instructions.md
	pandoc -f markdown -t html subject_instructions.md -s -o subject_instructions.html


instructions: subject_instructions.html
	xdg-open subject_instructions.html

instructpdf: subject_instructions.pdf
	xdg-open subject_instructions.pdf

subject_instructions.pdf: subject_instructions.md
	pandoc subject_instructions.md --template fonts/latex.template.tex -o subject_instructions.pdf



calib:
	python calibrate.py



showcalib:
	@echo "Existing calibration files:"
	ls data/calib_*

soundtest:
	python soundtest.py



list:
	@echo "Listing the input devices (pick the joystick with -event- "
	ls /dev/input/by-id/*event*



mni:       # setup used at the MNI
	ln -fs "/dev/input/by-id/usb-Current_Designs__Inc._932_R712-if02-event-joystick" joystick-event
#ln -fs "/dev/input/by-id/usb-Current_Designs__Inc._932_R385-if02-event-joystick" joystick-event # This was previously

douglas:   # setup used at the Douglas
	ln -fs "/dev/input/by-id/usb-Current_Designs__Inc._932_R710-if02-event-joystick" joystick-event

logitech: # setup used with Logitech joystick
	ln -fs "/dev/input/by-id/usb-Logitech_Logitech_Extreme_3D-event-joystick" joystick-event

mcl: # Joystick used at the motor control lab (MCL)
	ln -fs "/dev/input/by-id/usb-Thrustmaster__Inc._USB_Game_Controllers-event-joystick" joystick-event
