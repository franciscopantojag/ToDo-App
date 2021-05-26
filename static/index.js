const myTodos = document.getElementById("myTodos");
if (myTodos) {
  const checkBoxes = document.querySelectorAll(
    "table[id='myTodos'] td[name='toDo.done'] input[type='checkbox']"
  );
  console.log();
  checkBoxes.forEach((checkBox) => {
    checkBox.onchange = async () => {
      checkBox.disabled = true;
      const { checked } = checkBox;
      await new Promise(resolve => setTimeout(resolve, 300))
      const recordId = checkBox.parentElement.getAttribute("record-id");
      const toDoNameElements = document.querySelectorAll(
        `table[id='myTodos'] td[name='toDo.toDo']`
      );
      let toDoNameElement;
      toDoNameElements.forEach((element) => {
        const recordIdToDoName = element.getAttribute("record-id");
        if (recordIdToDoName === recordId) {
          toDoNameElement = element;
        }
      });
      if (toDoNameElement) {
        //ajax
        let message;
        try {
          const response = await fetch(`/toDos/${recordId}/done`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              checked,
            }),
          });
          message = await response.json();
        } catch (error) {
          console.log(error);
        }
        if (checkBox.checked && message?.done) {
          toDoNameElement.classList.add("line-through");
        } else if (!checkBox.checked && message?.done) {
          toDoNameElement.classList.remove("line-through");
        }
      }
      checkBox.disabled = false;
    };
  });
}
