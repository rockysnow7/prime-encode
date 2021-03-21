from typing import List
from tqdm import tqdm
from itertools import product, chain
from operator import mul
from functools import reduce
from math import floor, ceil, sqrt
from sympy import prime, isprime, primefactors, primerange


# main
def encode_str(text: str, repeat: bool=False) -> str:
	utf_bits, num_split_chars = 16, 2

	text = [ord(char) for char in text]
	#print("text:", [i for i in text])
	text_offset = min(text)
	text_offset_bytes = int_to_bytes(text_offset, utf_bits, num_split_chars)
	text = [i-text_offset+1 for i in text]

	if repeat:
	    num_repeats = text[0]
	else:
	    num_repeats = num_split_chars

	append_min = False
	if len(text) % 2 == 1:
	    append_min = True
	    text.append(min(text))
	append_min = int_to_bytes(int(append_min), utf_bits, num_split_chars)

	primes = [prime(i) for i in tqdm(text)]
	#print("primes:", primes)

	# [1 or 0 (asc or des)]
	orders = [int(primes[i] < primes[i+1]) for i in range(0, len(primes), 2)]
	#print("orders_bits:", orders)
	orders = "0b1" + "".join([str(i) for i in orders])
	#print("orders_bin:", orders)
	orders = int(orders, 2)
	#print("orders_int:", orders)
	orders = int_to_bytes(orders, utf_bits, num_split_chars)
	#print("orders_bytes:", orders)

	semiprimes = [primes[i]*primes[i+1] for i in range(0, len(primes), 2)]
	semiprimes_hash = int_to_bytes(hash(tuple(semiprimes)), utf_bits, num_split_chars)
	print("semiprimes:", semiprimes)
	semiprimes_offset = min(semiprimes)-1
	print("semiprimes_offset:", semiprimes_offset)
	semiprimes_offset_bytes = int_to_bytes(semiprimes_offset, utf_bits, num_split_chars)
	semiprimes = [i-semiprimes_offset for i in semiprimes]
	#print("semiprimes:", semiprimes)

	d = ceil(max(semiprimes)/(2**utf_bits - num_split_chars))  # divisor
	d_bytes = int_to_bytes(d, utf_bits, num_split_chars)

	semiprimes_small = [round(i/d)+num_split_chars for i in semiprimes]

	final = [num_repeats, *append_min, *semiprimes_hash, 1, *semiprimes_offset_bytes, 1, *text_offset_bytes, 1, *d_bytes, 1, *orders, 1, *semiprimes_small]
	#print("final:", final)
	final = "".join([chr(char) for char in final])

	return final


def decode_str(text: str) -> str:
	utf_bits, num_split_chars = 16, 2

	text = [ord(char) for char in text]

	num_repeats = text[0] - num_split_chars + 1
	for i in tqdm(range(num_repeats)):
		text = split_list(text, 1)
		append_min = bool(bytes_to_int([text[0][1]], num_split_chars))
		text[0] = text[0][2:]

		semiprimes_hash = bytes_to_int(text[0], num_split_chars)
		semiprimes_offset = bytes_to_int(text[1], num_split_chars)
		text_offset = bytes_to_int(text[2], num_split_chars)
		#print("min_offset:", min_offset)
		#print("semiprimes_hash:", semiprimes_hash)
		d = bytes_to_int(text[3], num_split_chars)
		#print("d:", d)

		#print("text[4]:", text[4])
		orders = bytes_to_int(text[4], num_split_chars)
		#print("orders_int:", orders)
		orders = bin(orders)
		#print("orders_bin:", orders)
		orders = orders[3:]
		#print("orders_bits:", orders)
		orders = [int(i) for i in orders]
		#print("orders:", orders)

		semiprimes_d = [d*(i-num_split_chars) for i in text[5]]
		#print("semiprimes_d:", semiprimes_d)

		#print("A")
		semiprimes_options = [[i+j+semiprimes_offset for j in range(round(-d/2), round(d/2)+1) if is_semiprime(i+j+semiprimes_offset)] for i in tqdm(semiprimes_d)]
		#print("semiprimes_options_info:", len(semiprimes_options), min(semiprimes_options), max(semiprimes_options))
		#print("semiprimes_options:", semiprimes_options)

		num_permutations = reduce(mul, [len(i) for i in semiprimes_options], 1)
		print(f"Searching {num_permutations} permutations")

		semiprimes = None
		i = 0
		for perm in tqdm(product(*semiprimes_options)):
			mes = f"perm {i}/{num_permutations} ({100*i/num_permutations}%)"
			print(mes, end=f"\r{' '*100}\r")

			perm_hash = abs(hash(perm))
			if perm_hash == semiprimes_hash:
				semiprimes = perm
				break
			i += 1
		#print("semiprimes:", semiprimes)

		if semiprimes is None:
			print(f"Cannot match hash {semiprimes_hash}")
			return None

		primes = [primefactors(i) for i in tqdm(semiprimes)]
		#print("primes:", primes)
		for j in tqdm(range(len(primes))):
			if len(primes[j]) == 1:
				primes[j] *= 2
			elif not orders[j]:
				primes[j] = reversed(primes[j])
		primes = list(chain(*primes))
		#print("primes:", primes)

		primes_range = list(primerange(2, max(primes)+1))
		chars = [primes_range.index(i)+text_offset for i in tqdm(primes)]
		if append_min:
			chars = chars[:-1]

		text = "".join([chr(i) for i in chars])
	#print("text:", [ord(i) for i in text])

	return text


# helper functions
def int_to_bytes(n: int, num_bits: int, offset: int=0) -> List[int]:
	n_bin = bin(abs(n))[2:]
	num_bits -= 1

	n_split = ["1"+n_bin[i:i+num_bits] for i in range(0, len(n_bin), num_bits)]
	n_ints = [int("0b" + i, 2)+offset for i in n_split]

	return n_ints

def bytes_to_int(ns: List[int], offset: int=0) -> int:
	ns = [n-offset for n in ns]
	for i in range(len(ns)):
		ns[i] = bin(ns[i])[3:]

	ns = "".join(ns)
	n = int("0b" + ns, 2)

	return n


def is_semiprime(n: int) -> bool:
	if n < 2:
		return False

	for a in range(2, floor(sqrt(n))+1):
	    if n % a == 0:
	        b = int(n/a)
	        return isprime(a) and isprime(b)
	return False


def split_list(lst: List[any], x: any) -> List[List[any]]:
	lsts = [[]]
	for i in lst:
	    if i == x:
	        lsts.append([])
	    else:
	        lsts[-1].append(i)

	lsts = [i for i in lsts if i != []]

	return lsts
