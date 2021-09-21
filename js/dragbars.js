/*
-*- coding: utf-8 -*-

-*- mode: js -*-

elf_diff

Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)

This program is free software: you can redistribute it and/or modify it under it under
the terms of the GNU General Public License as published by the Free Software
Foundation, version 3.

This program is distributed in the hope that it will be useful, but WITHOUT but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with along with
this program. If not, see <http://www.gnu.org/licenses/>.

*/
let isHorizDragging = false;
let isVertDragging = false;

/*
function ResetColumnSizes() {
	// when page resizes return to default col sizes
	let page = document.getElementById("pageFrame");
	page.style.gridTemplateColumns = "2fr 6px 6fr 6px 2fr";
}
*/

function SetPointerEvents(type) {
	document.getElementById("overview").style['pointer-events'] = type;
  document.getElementById("details").style['pointer-events'] = type;
}

function StartHorizDrag(event) {
		
		event.preventDefault();
	//console.log("mouse down");
	isHorizDragging = true;
	
	SetPointerEvents('none');
}

function StartVertDrag(event) {
		
		event.preventDefault();
	console.log("starting vert");
	isVertDragging = true;
	SetPointerEvents('none');
}

function EndDrag(event) {
		event.preventDefault();
	console.log("mouse up");
	isHorizDragging = false;
	isVertDragging = false;
	SetPointerEvents('auto');
}

function OnDrag(event) {
	if(isHorizDragging || isVertDragging) {
		event.preventDefault();
		console.log("Dragging");
		
		let dragbarWidth = 2;
		
		let container = document.getElementById("container");
		
		if(isHorizDragging) {
		
		  let sideCol = document.getElementById("side");
		  let rightCol = document.getElementById("overview");	
		
		  let sideColWidth = event.clientX;
		  let rightColWidth = container.offsetWidth - sideColWidth - dragbarWidth;
				
			let cols = [
				sideColWidth,
				dragbarWidth,
				rightColWidth
			];
			
			let newColDefn = cols.map(c => c.toString() + "px").join(" ");
		
		  container.style.gridTemplateColumns = newColDefn;
		}
		
		if(isVertDragging) {
      let vMargins = 10;
      let headerMargins = vMargins;
      let footerMargins = vMargins;

			let headerRow = document.getElementById("header");
			let overviewRow = document.getElementById("overview");
			let detailsRow = document.getElementById("details");
			let footerRow = document.getElementById("footer");

      let headerHeight = headerRow.offsetHeight + headerMargins;
      let footerHeight = footerRow.offsetHeight + footerMargins;
			
			let overviewRowHeight = event.clientY - headerHeight;
			let detailsRowHeight = container.offsetHeight - headerHeight - footerHeight - overviewRowHeight - dragbarWidth;

			let rows = [
				headerHeight,
				overviewRowHeight,
				dragbarWidth,
				detailsRowHeight,
				footerHeight
			];

			let newRowDefn = rows.map(c => c.toString() + "px").join(" ");
			container.style.gridTemplateRows = newRowDefn;
		}
	}
}
