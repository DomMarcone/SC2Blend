import bpy
import bmesh


def read_sc2(context, filepath, use_some_setting):
	#
	#written by Dominic Marcone
	#
	#thanks to David Moews for being the Rosetta Stone of the *.SC2 file.
	#
	#filename = 'all/calebopo.sc2'
	#filename = 'all/CFCopolis.sc2'
	#filename = "DOMSBURG.SC2"
	#
	filename = filepath
	#
	#rotate the data before processing
	rotateWorld = 0
	#
	#rotate level data
	def rotateData( r, input ) :
		output = [None] * 128 * 128
		#
		if r == 0 :
			return input
		#
		for j in range( 0, 128 ) :
			for i in range( 0, 128 ) :
				#
				if r == 1 :
					newX = 127 - j
					newY = i
				#
				if r == 2 :
					newX = 127 - i
					newY = 127 - j
				#
				if r == 3 :
					newX = j
					newY = 127 - i
				#
				output[ j * 128 + i ] = input[ newY * 128 + newX ]
		#
		return output
	#
	#
	#stolen straight from the example script
	def addUV( uv ):
		obj = bpy.context.active_object
		me = obj.data
		bm = bmesh.from_edit_mesh( me )
		#
		uv_layer = bm.loops.layers.uv.verify()
		bm.faces.layers.tex.verify()  # currently blender needs both layers.
		#
		count = 0
		#
		# adjust UVs
		for f in bm.faces:
			for l in f.loops:
				luv = l[uv_layer]
				if luv.select:
					# apply the location of the vertex as a UV
					luv.uv = uv[count]
					count += 1
		#
		bmesh.update_edit_mesh(me)
		#
		#
	#
	class Segment :
		def __init__( self, name, length, rawContent ):
			self.name = name
			self.length = length
			self.rawContent = rawContent
			#
			#time to convert...
			self.content = rawContent
			#
			self.content = content
			#
		def getName( self ):
			return self.name
		#
		def getLength( self ) :
			return self.length
		#
		def getContent( self ) :
			return self.content
	#
	#
	def uncompress( input ) :
		#
		output = []
		#
		i = 0
		while i < len( input ) :
			mult = input[ i ]
			i += 1
			#
			if mult < 128 :
				for j in range( 0, mult ) :
					term = input[ i ]
					output.append( term )
					i += 1
			#
			if mult >= 128 : 
				term = input[ i ]
				i += 1
				for j in range( 0, mult - 127 ) :
					output.append( term )
		return output
	#
	#
	def loadModel( verts, uvs, faces, filename, translate, rotate ) :
		#
		tempVerts = []
		tempUVs = []
		tempFaces = []
		#
		file = open( "{}sc2_blocks\\{}".format( bpy.path.abspath("//"), filename ) )
		#
		rotate &= 3
		#
		parse = file.readline()
		#   print("reading line: {}".format( parse ) )
		while len( parse ) > 1:
			token = parse.split()
			if token[0] == 'v' :
				#print( "parsing vert" )
				if rotate == 0 :
					x = -float( token[1] ) + translate[0]
					y = -float( token[2] ) + translate[1]
				#
				if rotate == 1 :
					x = -float( token[2] ) + translate[0]
					y = float( token[1] ) + translate[1]
				#
				if rotate == 2 :
					x = float( token[1] ) + translate[0]
					y = float( token[2] ) + translate[1]
				#
				if rotate == 3 :
					x = float( token[2] ) + translate[0]
					y = -float( token[1] ) + translate[1]
				#
				tempVerts.append( [ ( x, y, float( token[3] ) + translate[2] ) ] )
			#
			if token[0] == 'vt' :
				#print( "parsing uv" )
				tempUVs.append( [ ( float( token[1] ), float( token[2] ) ) ] )
			#
			if token[0] == 'f' :
				#print( "parsing f" )
				vertPos = len( verts )
				#
				v1, u1 = token[1].split("/")
				v2, u2 = token[2].split("/")
				v3, u3 = token[3].split("/")
				#
				verts.extend( tempVerts[ int(v1) - 1 ] ) 
				verts.extend( tempVerts[ int(v2) - 1 ] ) 
				verts.extend( tempVerts[ int(v3) - 1 ] ) 
				#
				uvs.extend( tempUVs[ int(u1) - 1 ] )
				uvs.extend( tempUVs[ int(u2) - 1 ] )
				uvs.extend( tempUVs[ int(u3) - 1 ] )
				#
				faces.extend( [ (vertPos + 0, vertPos + 1, vertPos + 2) ] )
				#
			parse = file.readline()
			#
		file.close()
	#
	#sc = open( "{}".format( filename ) )
	sc = open( filename )
	#
	seg = []
	#
	scraw = sc.buffer.raw
	#
	print( "OPENING:{}".format( scraw.name ) )
	#
	fileEnd = scraw.seek(0,2)
	#
	scraw.seek(12)
	#
	while scraw.seek(0,1) < fileEnd:
		name = scraw.read(4)
		length = int.from_bytes( scraw.read(4), byteorder='big' )
		print( "loading segment:{} : {}".format( name, length ) )
		content = scraw.read( length )
		seg.append( Segment( name.decode(), length, content ) )
	#
	sc.close()
	#
	alt = []
	piece = [None] * 128 * 128
	rot = [0] * 128 * 128
	water_level = 0 #this will set the minimum altitude at the end
	#
	cityName = None
	#
	for s in seg :
		name = s.getName()
		content = s.getContent()
		#
		if name == 'CNAM' :
			try :
				cityName = content.decode()
			except :
				cityName = "unknown"
			#
			print( "City Name:{}".format( cityName ) )
		#
		#Altitude map (heights)
		if name == 'ALTM' :
			#
			print( "processing ALTM" )
			#
			for j in range( 0, 128 ) :
				for i in range( 0, 128 ) :
					tile = content[ 2*( j*128 + i ) ]
					tile *= 256
					tile += content[ 2*( j*128 + i ) + 1 ]
					#
					tile &= 31
					#
					alt.append( tile )
					#
			alt = rotateData( rotateWorld, alt )
			#
		#
		if name == 'XTER' :
			#
			print( "processing XTER" )
			#
			mesh = bpy.data.meshes.new( "XTER" )
			object = bpy.data.objects.new( "XTER", mesh )
			#
			vert = []
			face = []
			#
			print( "XTER compressed size  : {}".format( len( content ) ) )
			#
			rawCont = uncompress( content )
			#
			rawCont = rotateData( rotateWorld, rawCont )
			#
			print( "XTER uncompressed size: {}".format( len( rawCont ) ) )
			#
			count = 0
			#
			for j in range( 0, 128 ) :
				for i in range( 0, 128 ) :
					#
					pos = j * 128 + i
					#
					p = rawCont[ pos ]
					#
					#p &= 15
					#
					#Grounds
					if p == 0 :
						piece[ pos ] = "ground_0000.obj"
					#
					if p == 1 :
						piece[ pos ] = "ground_0011.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 2 :
						piece[ pos ] = "ground_0011.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 3 :
						piece[ pos ] = "ground_0011.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 4 :
						piece[ pos ] = "ground_0011.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 5 :
						piece[ pos ] = "ground_0111.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 6 :
						piece[ pos ] = "ground_0111.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 7 :
						piece[ pos ] = "ground_0111.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 8 :
						piece[ pos ] = "ground_0111.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 9 :
						piece[ pos ] = "ground_0001.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 10 :
						piece[ pos ] = "ground_0001.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 11 :
						piece[ pos ] = "ground_0001.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 12 :
						piece[ pos ] = "ground_0001.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 13 :
						alt[ pos ] += 1
					if p == 14 :
						alt[ pos ] += 1
					if p == 15 :
						alt[ pos ] += 1
					#
					#
					if 16 <= p and p < 32 :
						piece[ pos ] = "water_1111.obj"
					#
					#water - just under the surface
					if p == 32 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 33 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 34 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 35 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 36 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 37 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 0 + rotateWorld
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 38 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 1 + rotateWorld
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 39 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 2 + rotateWorld
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 40 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 3 + rotateWorld
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 41 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 42 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 43 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 44 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 45 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					if p == 46 :
						piece[ pos ] = "water_1111.obj"
						alt[ pos ] += 1
						water_level = alt[ pos ]
					#
					#
					if p == 48 :
						piece[ pos ] = "water_1111.obj"
					if p == 49 :
						piece[ pos ] = "water_1111.obj"
					if p == 50 :
						piece[ pos ] = "water_1111.obj"
					if p == 51 :
						piece[ pos ] = "water_1111.obj"
					if p == 52 :
						piece[ pos ] = "water_1111.obj"
					if p == 53 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 0 + rotateWorld
					if p == 54 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 1 + rotateWorld
					if p == 55 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 2 + rotateWorld
					if p == 56 :
						piece[ pos ] = "water_0011.obj"
						rot[ pos ] = 3 + rotateWorld
					if p == 57 :
						piece[ pos ] = "water_1111.obj"
					if p == 58 :
						piece[ pos ] = "water_1111.obj"
					if p == 59 :
						piece[ pos ] = "water_1111.obj"
					if p == 60 :
						piece[ pos ] = "water_1111.obj"
					#
					#
					if p == 62 :
						piece[ pos ] = "water_fall.obj"
					if p == 64 :
						piece[ pos ] = "water_0101.obj"
						rot[ pos ] = 0
					if p == 65 :
						piece[ pos ] = "water_0101.obj"
						rot[ pos ] = 1
					if p == 66 :
						piece[ pos ] = "water_0001.obj"
						rot[ pos ] = 0
					if p == 67 :
						piece[ pos ] = "water_0001.obj"
						rot[ pos ] = 1
					if p == 68 :
						piece[ pos ] = "water_0001.obj"
						rot[ pos ] = 2
					if p == 69 :
						piece[ pos ] = "water_0001.obj"
						rot[ pos ] = 3
		#
		#
		#buildings
		if name == 'XBLD' :
			print( "processing XBLD" )
			#
			print( "XBLD compressed size  : {}".format( len( content ) ) )
			#
			rawCont = uncompress( content )
			#
			rawCont = rotateData( rotateWorld, rawCont )
			#
			print( "XBLD uncompressed size: {}".format( len( rawCont ) ) )
			#
			for j in range( 0, 128 ) :
				for i in range( 0, 128 ) :
					#
					pos = j * 128 + i
					size = 1
					type = piece[ pos ]
					#
					p = rawCont[ pos ]
					#
					#rubble
					if p == 1 :
						type = "rubble_0.obj"
					if p == 2 :
						type = "rubble_1.obj"
					if p == 3 :
						type = "rubble_2.obj"
					if p == 4 :
						type = "rubble_3.obj"
					#
					#Trees
					if p == 6 :
						if piece[ pos ] == "ground_0000.obj" :
							type = "tree_0_0000.obj"
						if piece[ pos ] == "ground_0001.obj" :
							type = "tree_0_0001.obj"
						if piece[ pos ] == "ground_0011.obj" :
							type = "tree_0_0011.obj"
						if piece[ pos ] == "ground_0111.obj" :
							type = "tree_0_0111.obj"
					#
					if p == 7 :
						if piece[ pos ] == "ground_0000.obj" :
							type = "tree_1_0000.obj"
						if piece[ pos ] == "ground_0001.obj" :
							type = "tree_1_0001.obj"
						if piece[ pos ] == "ground_0011.obj" :
							type = "tree_1_0011.obj"
						if piece[ pos ] == "ground_0111.obj" :
							type = "tree_1_0111.obj"
					#
					if p == 8 :
						if piece[ pos ] == "ground_0000.obj" :
							type = "tree_2_0000.obj"
						if piece[ pos ] == "ground_0001.obj" :
							type = "tree_2_0001.obj"
						if piece[ pos ] == "ground_0011.obj" :
							type = "tree_2_0011.obj"
						if piece[ pos ] == "ground_0111.obj" :
							type = "tree_2_0111.obj"
					#
					if p == 9 :
						if piece[ pos ] == "ground_0000.obj" :
							type = "tree_3_0000.obj"
						if piece[ pos ] == "ground_0001.obj" :
							type = "tree_3_0001.obj"
						if piece[ pos ] == "ground_0011.obj" :
							type = "tree_3_0011.obj"
						if piece[ pos ] == "ground_0111.obj" :
							type = "tree_3_0111.obj"
					#
					if p == 10 :
						if piece[ pos ] == "ground_0000.obj" :
							type = "tree_4_0000.obj"
						if piece[ pos ] == "ground_0001.obj" :
							type = "tree_4_0001.obj"
						if piece[ pos ] == "ground_0011.obj" :
							type = "tree_4_0011.obj"
						if piece[ pos ] == "ground_0111.obj" :
							type = "tree_4_0111.obj"
					#
					if p == 11 :
						if piece[ pos ] == "ground_0000.obj" :
							type = "tree_5_0000.obj"
						if piece[ pos ] == "ground_0001.obj" :
							type = "tree_5_0001.obj"
						if piece[ pos ] == "ground_0011.obj" :
							type = "tree_5_0011.obj"
						if piece[ pos ] == "ground_0111.obj" :
							type = "tree_5_0111.obj"
					#
					if p == 12 :
						if piece[ pos ] == "ground_0000.obj" :
							type = "tree_6_0000.obj"
						if piece[ pos ] == "ground_0001.obj" :
							type = "tree_6_0001.obj"
						if piece[ pos ] == "ground_0011.obj" :
							type = "tree_6_0011.obj"
						if piece[ pos ] == "ground_0111.obj" :
							type = "tree_6_0111.obj"
					#
					#Powerlines
					if p == 14 :
						type = "wire_0101.obj"
						rot[ pos ] = 1 + rotateWorld
					if p == 15 :
						type = "wire_0101.obj"
						rot[ pos ] = 0 + rotateWorld
					if p == 16 :
						type = "wire_hill.obj"
					if p == 17 :
						type = "wire_hill.obj"
					if p == 18 :
						type = "wire_hill.obj"
					if p == 19 :
						type = "wire_hill.obj"
					#
					if p == 20 :
						type = "wire_0011.obj"
						rot[ pos ] = 3 + rotateWorld
					if p == 21 :
						type = "wire_0011.obj"
						rot[ pos ] = 0 + rotateWorld
					if p == 22 :
						type = "wire_0011.obj"
						rot[ pos ] = 1 + rotateWorld
					if p == 23 :
						type = "wire_0011.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 24 :
						type = "wire_0111.obj"
						rot[ pos ] = 3 + rotateWorld
					if p == 25 :
						type = "wire_0111.obj"
						rot[ pos ] = 0 + rotateWorld
					if p == 26 :
						type = "wire_0111.obj"
						rot[ pos ] = 1 + rotateWorld
					if p == 27 :
						type = "wire_0111.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 28 :
						type = "wire_1111.obj"
					#
					#Roads
					if p == 29 :
						type= "road_0101.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 30 :
						type = "road_0101.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 31 :
						type = "road_hill.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 32 :
						type = "road_hill.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 33 :
						type = "road_hill.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 34 :
						type = "road_hill.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 35 :
						type = "road_0011.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 36 :
						type = "road_0011.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 37 :
						type = "road_0011.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 38 :
						type = "road_0011.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 39 :
						type = "road_0111.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 40 :
						type = "road_0111.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 41 :
						type = "road_0111.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 42 :
						type = "road_0111.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 43 :
						type = "road_1111.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					#rails
					if p == 44 :
						type= "rail_0101.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 45 :
						type = "rail_0101.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 46 :
						type = "rail_hill1.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 47 :
						type = "rail_hill1.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 48 :
						type = "rail_hill1.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 49 :
						type = "rail_hill1.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 50 :
						type = "rail_0011.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 51 :
						type = "rail_0011.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 52 :
						type = "rail_0011.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 53 :
						type = "rail_0011.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 54 :
						type = "rail_0111.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					if p == 55 :
						type = "rail_0111.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 56 :
						type = "rail_0111.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 57 :
						type = "rail_0111.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 58 :
						type = "rail_1111.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 59 :
						type = "rail_hill0.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 60 :
						type = "rail_hill0.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					if p == 61 :
						type = "rail_hill0.obj"
						rot[ pos ] = 2 + rotateWorld
					#
					if p == 62 :
						type = "rail_hill0.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					#
					#Crossings
					if p == 67 :
						type = "wire_road.obj"
						rot[ pos ] = 0 + rotateWorld
					if p == 68 :
						type = "wire_road.obj"
						rot[ pos ] = 1 + rotateWorld
					if p == 69 :
						type = "rail_road.obj"
						rot[ pos ] = 1 + rotateWorld
					if p == 70 :
						type = "rail_road.obj"
						rot[ pos ] = 0 + rotateWorld
					#
					if p == 71 :
						type = "wire_rail.obj"
						rot[ pos ] = 0 + rotateWorld
					if p == 72 :
						type = "wire_rail.obj"
						rot[ pos ] = 1 + rotateWorld
					#
					#suspension bridges
					if p == 81 or p == 82 or p == 84 or p == 85:
						last = piece[ pos - 128 ]
						if last == "bridge_causway_0.obj" or last == "bridge_suspension_0.obj" or last == "road_hill.obj" :
							rot[ pos ] = 1 + rotateWorld
						type = "bridge_causway_0.obj"
					#
					if p == 83 :
						last = piece[ pos - 128 ]
						if last == "bridge_causway_0.obj" or last == "bridge_suspension_0.obj" or last == "road_hill.obj" :
							rot[ pos ] = 1 + rotateWorld
						type = "bridge_suspension_0.obj"
					#
					#causeway bridges
					if p == 87 or p == 88 or p == 89 :
						last = piece[ pos - 128 ]
						if last == "bridge_causway_0.obj" or "bridge_causway_1.obj" or last == "bridge_suspension_0.obj" or last == "road_hill.obj" :
							rot[ pos ] = 1 + rotateWorld
						type = "bridge_causway_0.obj"
					#
					if p == 86 :
						last = piece[ pos - 128 ]
						if last == "bridge_causway_0.obj" or "bridge_causway_1.obj" or last == "bridge_suspension_0.obj" or last == "road_hill.obj" :
							rot[ pos ] = 1 + rotateWorld
						type = "bridge_causway_1.obj"
					#
					#wire bridges
					if p == 92 :
						last = piece[ pos - 128 ]
						if last == "bridge_wire.obj" or last == "wire_hill.obj" :
							rot[ pos ] = 1 + rotateWorld
						type = "bridge_wire.obj"
					#
					#
					#sub-rail
					if p == 108 :
						type = "rail_tosubway.obj"
						rot[ pos ] = 0 + rotateWorld
					if p == 109 :
						type = "rail_tosubway.obj"
						rot[ pos ] = 1 + rotateWorld
					if p == 110 :
						type = "rail_tosubway.obj"
						rot[ pos ] = 2 + rotateWorld
					if p == 111 :
						type = "rail_tosubway.obj"
						rot[ pos ] = 3 + rotateWorld
					#
					#residential 1x1
					if p == 112 :
						type = "res_00.obj"
					if p == 113 :
						type = "res_01.obj"
					if p == 114 :
						type = "res_02.obj"
					if p == 115 :
						type = "res_03.obj"
					if p == 116 :
						type = "res_04.obj"
					if p == 117 :
						type = "res_05.obj"
					if p == 118 :
						type = "res_06.obj"
					if p == 119 :
						type = "res_07.obj"
					if p == 120 :
						type = "res_08.obj"
					if p == 121 :
						type = "res_09.obj"
					if p == 122 :
						type = "res_0A.obj"
					if p == 123 :
						type = "res_0B.obj"
					#
					#comercial 1x1
					if p == 124 :
						type = "com_00.obj"
					if p == 125 :
						type = "com_01.obj"
					if p == 126 :
						type = "com_02.obj"
					if p == 127 :
						type = "com_03.obj"
					if p == 128 :
						type = "com_04.obj"
					if p == 129 :
						type = "com_05.obj"
					if p == 130 :
						type = "com_06.obj"
					if p == 131 :
						type = "com_07.obj"    
					#
					#
					#industrial 1x1
					if p == 132 :
						type = "ind_00.obj"
					if p == 133 :
						type = "ind_01.obj"
					if p == 134 :
						type = "ind_02.obj"
					if p == 135 :
						type = "ind_03.obj"
					#
					#construction 1x1
					if p == 136 :
						type = "construction_00.obj"
					if p == 137 :
						type = "construction_01.obj"
					#
					#abandoned 1x1
					if p == 138 :
						type = "abandoned_00.obj"
					if p == 139 : 
						type = "abandoned_01.obj"
					#
					#residential 2x2
					if p == 140 :
						type = "res_10.obj"
						size = 2
					if p == 141 :
						type = "res_11.obj"
						size = 2
					if p == 142 :
						type = "res_12.obj"
						size = 2
					if p == 143 :
						type = "res_13.obj"
						size = 2
					if p == 144 :
						type = "res_14.obj"
						size = 2
					if p == 145 :
						type = "res_15.obj"
						size = 2
					if p == 146 :
						type = "res_16.obj"
						size = 2
					if p == 147 :
						type = "res_17.obj"
						size = 2
					#
					#comercial 2x2
					if p == 148 :
						type = "com_10.obj"
						size = 2
					if p == 149 :
						type = "com_11.obj"
						size = 2
					if p == 150 :
						type = "com_12.obj"
						size = 2
					if p == 151 :
						type = "com_13.obj"
						size = 2
					if p == 152 :
						type = "com_14.obj"
						size = 2
					if p == 153 :
						type = "com_15.obj"
						size = 2
					if p == 154 :
						type = "com_16.obj"
						size = 2
					if p == 155 :
						type = "com_17.obj"
						size = 2
					if p == 156 :
						type = "com_18.obj"
						size = 2
					if p == 157 :
						type = "com_19.obj"
						size = 2
					#
					#industrial 2x2
					if p == 158 :
						type = "ind_10.obj"
						size = 2
					if p == 159 :
						type = "ind_11.obj"
						size = 2
					if p == 160 :
						type = "ind_12.obj"
						size = 2
					if p == 161 :
						type = "ind_13.obj"
						size = 2
					if p == 162 :
						type = "ind_14.obj"
						size = 2
					if p == 163 :
						type = "ind_15.obj"
						size = 2
					if p == 164 :
						type = "ind_16.obj"
						size = 2
					if p == 165 :
						type = "ind_17.obj"
						size = 2
					#
					#construction 2x2
					if p == 166 :
						type = "construction_10.obj"
						size = 2
					if p == 167 :
						type = "construction_11.obj"
						size = 2
					if p == 168 or p == 169 :
						type = "construction_12.obj"
						size = 2
					#
					#abandoned 2x2
					if p == 170 :
						type = "abandoned_02.obj"
						size = 2
					if p == 171 :
						type = "abandoned_03.obj"
						size = 2
					if p == 172 :
						type = "abandoned_04.obj"
						size = 2
					if p == 173 :
						type = "abandoned_05.obj"
						size = 2
					#
					#residential 3x3
					if p == 174 :
						type = "res_20.obj"
						size = 3
					if p == 175 :
						type = "res_21.obj"
						size = 3
					if p == 176 :
						type = "res_22.obj"
						size = 3
					if p == 177 :
						type = "res_23.obj"
						size = 3
					#
					#comercial 3x3
					if p == 178 :
						type = "com_20.obj"
						size = 3
					if p == 179 :
						type = "com_21.obj"
						size = 3
					if p == 180 :
						type = "com_22.obj"
						size = 3
					if p == 181 :
						type = "com_23.obj"
						size = 3
					if p == 182 :
						type = "com_24.obj"
						size = 3
					if p == 183 :
						type = "com_25.obj"
						size = 3
					if p == 184 :
						type = "com_26.obj"
						size = 3
					if p == 185 :
						type = "com_27.obj"
						size = 3
					if p == 186 :
						type = "com_28.obj"
						size = 3
					if p == 187  :
						type = "com_29.obj"
						size = 3
					#
					#industrial 3x3
					if p == 188 :
						type = "ind_20.obj"
						size = 3
					if p == 189 :
						type = "ind_21.obj"
						size = 3
					if p == 190 :
						type = "ind_22.obj"
						size = 3
					if p == 191 :
						type = "ind_23.obj"
						size = 3
					if p == 192 :
						type = "ind_24.obj"
						size = 3
					if p == 193 :
						type = "ind_25.obj"
						size = 3
					#
					#construction 3x3
					if p == 194 :
						type = "construction_20.obj"
						size = 3
					if p == 195 :
						type = "construction_21.obj"
						size = 3
					#
					#
					#abandoned buildings 3x3
					if p == 196 :
						type = "abandoned_06.obj"
						size = 3
					if p == 197 :
						type = "abandoned_07.obj"
						size = 3
					#
					#
					#power plants
					if p == 198 :
						type = "power_dam.obj"
						rot[ pos ] = 1
					if p == 199 :
						type = "power_dam.obj"
						rot[ pos ] = 0
					if p == 200 :
						type = "power_wind.obj"
					if p == 201 :
						type = "power_gas.obj"
						size = 4
					if p == 202 :
						type = "power_oil.obj"
						size = 4
					if p == 203 :
						type = "power_nuclear.obj"
						size = 4
					if p == 204 :
						type = "power_solar.obj"
						size = 4
					if p == 205 :
						type = "power_microwave.obj"
						size = 4
					if p == 206 :
						type = "power_fusion.obj"
						size = 4
					if p == 207 :
						type = "power_coal.obj"
						size = 4
					#
					#
					if p == 208 :
						type = "cityhall.obj"
						size = 3
					#
					if p == 209 :
						#HOSPITAL
						type = "hospital.obj"
						size = 3
					#
					if p == 210 :
						#POLICE STATION
						type = "police_station.obj"
						size = 3
					#
					if p == 211 :
						#FIRE STATION
						type = "fire_station.obj"
						size = 3
					#
					if p == 212 :
						type = "museum.obj"
						size = 3
					#
					if p == 213 :
						type = "bigpark.obj"
						size = 3
					#
					if p == 214 :
						type = "school.obj"
						size = 3
					#
					if p == 215 :
						type = "stadium.obj"
						size = 4
					#
					if p == 216 : 
						type = "prison.obj"
						size = 4
					#
					if p == 217 :
						type = "college.obj"
						size = 4
					#
					if p == 218 :
						type = "zoo.obj"
						size = 4
					#
					if p == 219 :
						type = "statue.obj"
					#
					if p == 220 :
						type = "water_pump.obj"
					#
					#air and sea ports
					if p == 224 :
						type = "seaport_crane.obj"
					#
					if p == 225 :
						type = "airport_controltower.obj"
					#
					if p == 227 :
						type = "seaport_warehouse.obj"
					#
					if p == 228 :
						type = "airport_building_0.obj"
					#
					if p == 229 :
						type = "airport_building_1.obj"
					#
					if p == 230 :
						type = "airport_tarmac.obj"
					#
					#	
					if p == 234 :
						type = "airport_radar.obj"
					#
					if p == 235 :
						type = "water_tower.obj"
						size = 2
					#
					if p == 236 :
						type = "bus_depot.obj"
						size = 2
					#
					if p == 237 :
						type = "rail_station.obj"
						size = 2
					#
					if p == 238 :
						type = "airport_parkinglot.obj"
						size = 2
					#
					if p == 240 :
						type = "seaport_loadingbay.obj"
						size = 2
					#
					if p == 242 :
						type = "seaport_cargolot.obj"
						size = 2
					#					
					if p == 243 :
						type = "mayors_house.obj"
						size = 2
					#
					if p == 244 :
						type = "water_treatment.obj"
						size = 2
					#
					if p == 245 :
						type = "library.obj"
						size = 2
					#
					if p == 246 :
						type = "airport_hangar.obj"
						size = 2				
					#
					if p == 247 :
						type = "church.obj"
						size = 2
					#
					if p == 248 :
						type = "marina.obj"
						size = 3
					#
					if p == 250 :
						type = "desalination.obj"
						size = 3
					#
					if p == 251 :
						type = "archology_plymouth.obj"
						size = 4
					if p == 252 :
						type = "archology_forest.obj"
						size = 4					
					if p == 253 :
						type = "archology_darco.obj"
						size = 4
					if p == 254 :
						type = "archology_launch.obj"
						size = 4
					if p == 255 :
						type = "braun_llama_dome.obj"
						size = 4
					#
					#delete other blocks which could become problematic
					for y in range( j, j+size) :
						for x in range( i, i+size ) :
							temp = y * 128 + x
							rawCont[temp] = None
							piece[temp] = None
					#
					piece[ (j + size - 1) * 128 + (i + size - 1) ] = type
		#
		#underground
		if name == 'XUND' :
			print( "processing XUND" )
			#
			print( "XUND compressed size  : {}".format( len( content ) ) )
			#
			rawCont = uncompress( content )
			#
			print( "XUND uncompressed size: {}".format( len( rawCont ) ) )
		#
	#
	#input("press enter to continue")
	#
	for i in range( 0, len( alt ) ) :
		if alt[ i ] < water_level :
			alt[ i ] = water_level
	#
	if cityName == None :
		cityName = "SimCity2000"
	#
	mesh = bpy.data.meshes.new( cityName.replace("\t","") )
	object = bpy.data.objects.new( cityName.replace("\t",""), mesh )
	#
	vert = []
	uv = []
	face = []
	#
	for j in range( 0, 128 ) :
		for i in range( 0, 128 ) :
			pos = j * 128 + i
			if piece[ pos ] != None :
				#loadModel( vert, uv, face, "{}\\sc2_blocks\\{}".format( bpy.path.abspath("//"), piece[ pos ] ), (-i*2 + 128, -j*2 + 128, alt[ pos ] ), rot[ pos ] )
				#print( "loading tile : {},{} ".format( i, j ) )
				loadModel( vert, uv, face, piece[ pos ], (-i*2 + 128, -j*2 + 128, 1.5 * alt[ pos ] -6 ) , rot[ pos ] )
	#
	#
	#
	bpy.context.scene.objects.link( object )
	mesh.from_pydata( vert, [], face )
	#
	uvMesh = mesh.uv_textures.new( name="UVMap" )
	#
	mesh.update( calc_edges=True )
	#
	bpy.context.scene.objects.active = object
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all( action='SELECT' )
	bpy.ops.uv.select_all( action='SELECT' )
	#
	addUV( uv )
	#
	object.location = [0, 0, 0]
	#
	bpy.ops.mesh.remove_doubles()
	#
	bpy.ops.object.mode_set(mode='OBJECT')
	#
	print( "finished loading {}".format( scraw.name ) )
	#
	#
	#
	return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportSC2(Operator, ImportHelper):
	"""This appears in the tooltip of the operator and in the generated docs"""
	bl_idname = "import_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
	bl_label = "Import SimCity 2000 .sc2"

	# ImportHelper mixin class uses this
	filename_ext = ".txt"

	filter_glob = StringProperty(
			default="*.sc2",
			options={'HIDDEN'},
			maxlen=255,  # Max internal buffer length, longer would be clamped.
			)

	# List of operator properties, the attributes will be assigned
	# to the class instance from the operator settings before calling.
	use_setting = BoolProperty(
			name="Example Boolean",
			description="Example Tooltip",
			default=True,
			)

	'''type = EnumProperty(
			name="Example Enum",
			description="Choose between two items",
			items=(('OPT_A', "First Option", "Description one"),
				   ('OPT_B', "Second Option", "Description two")),
			default='OPT_A',
			)'''

	def execute(self, context):
		return read_sc2(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
	self.layout.operator(ImportSC2.bl_idname, text="SimCity2000(.sc2)")


def register():
	bpy.utils.register_class(ImportSC2)
	bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
	bpy.utils.unregister_class(ImportSC2)
	bpy.types.INFO_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
	register()

	# test call
	#bpy.ops.import_test.some_data('INVOKE_DEFAULT')
