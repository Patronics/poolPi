


main:
pause 500
'touch C.4, b2
touch16 [%00010001],C.4,w2
pause 25
'sertxd ("UUU TouchValue: ",#w2,lf)
serout 0,T4800_4,("UUU TouchValue: ",#w2,lf)  'non inverted, as raspberry pi expects.
goto main